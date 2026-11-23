# Deployment Optimization — 502 & Latency Remediation

Status: complete — deployed and verified
Date: 2026-11-20
Target: `https://cbc-099068d6.fastapicloud.dev`

---

## 1. Observed symptoms

- `POST /api/v1/adaptive-quiz` returns **502** after ~8 s (body `EOF`).
- The next request returns **502** with `dial tcp ...: connect: connection refused`.
- Static routes still work, but the container takes ~10 s to boot.
- Everything is slow because the container is restarted on nearly every quiz call.

## 2. Measurements

Local, cold process (`.venv`, CPython 3.14.3, Windows):

| Stage | Time | RSS after |
|---|---|---|
| bare interpreter | — | 21 MB |
| `import main` (FastAPI app) | 3.0 s | 59 MB |
| `import sentence_transformers` | **37.0 s** | **472 MB** |
| load MiniLM | 1.8 s | 583 MB |
| encode one query | 1.5 s | 587 MB |
| Pinecone connect + query | 4.0 s | 589 MB |
| **first request, total** | **~60 s** | **~590 MB** |

Warm, in-process:

| Stage | Time |
|---|---|
| retrieval (cached model) | 0.38 s |
| `_call_groq` (single call) | 4.14 s |
| `generate_quiz` (full) | 5.50 s |

Live deployment probes:

| Request | Result |
|---|---|
| `GET /` | 200, 1.1 s |
| `POST /adaptive-quiz` | 502, 8.1 s, body `EOF` |
| following request | 502, `connection refused` |
| `GET /teacher/bands` | 200, 10.2 s (fresh boot) |
| 3x quiz retry | all died |

## 3. Root cause

`/adaptive-quiz` is the only route that touches torch, and it imports it lazily
inside `retriever._get_model()`. That import alone costs **413 MB** and ~37 s.

Sequence on the deployed container:

1. Container boots with ~59 MB resident.
2. First quiz request imports torch + transformers → ~590 MB.
3. Container hits its memory ceiling → SIGKILL → proxy sees `EOF` (502).
4. Container restarts; the next request is cold again.
5. Nothing is ever warm, so every call repeats steps 1-4.

The LLM is not implicated: Groq returns in ~4 s and the full pipeline is 5.5 s
once the model is resident.

## 4. Remediation

### Phase 0 — confirm the ceiling

Check the FastAPI Cloud dashboard memory limit and the request logs for
`Killed` / `OOMKilled`. A 512 MB limit makes Phase 1 mandatory.

### Phase 1 — remove torch from the request path

`retriever.build_query()` is deterministic: it only depends on
`(strand, sub_strand, band)`. `resolve_location` validates against a fixed
vocabulary (3 strands, 14 sub-strands) and there are 4 bands, so the entire
query space is **18 location combos x 4 bands = 72 strings**.

**Chosen approach — precomputed query-vector cache.**

- `generator/build_query_vectors.py` (offline, uses sentence-transformers)
  enumerates every reachable query string, embeds it, and writes
  `services/query_vectors.json` (base64 float32, ~150 KB).
- `retriever.py` replaces `_get_model().encode(...)` with a dict lookup and
  deletes `_get_model()` entirely.
- Cache miss falls through to the existing static-guidance guardrail.

Why this over fastembed: exact vector parity by construction (same model, same
query string, just precomputed), zero runtime ML dependency, no 90 MB model
download on every cold container, and no re-indexing of the 149 vectors.

### Phase 2 — slim the image

Verified by grep: `xgboost`, `scikit-learn`, `joblib`, `pandas`, `kagglehub`,
`pypdf`, `pymupdf`, `pdf2image`, `pytesseract` are used only by `predictor/*`
and `generator/*` scripts. Nothing in `services/` or `routers/` imports them.
`langchain*` is imported nowhere at all.

Move them to `[dependency-groups] dev`. This drops the multi-GB `nvidia-*` /
CUDA stack that the Linux torch wheel pulls in, and should cut container boot
from ~10 s to ~2-3 s.

### Phase 3 — harden the endpoint

- Warm the query-vector cache in a FastAPI `lifespan` startup hook.
- Pass an explicit `timeout` to the Pinecone query so a slow index degrades to
  the static fallback instead of hanging.
- Keep the `except Exception -> static guidance` guardrail as the safety net.

### Phase 4 — verify

1. `uv lock` (the `--locked` deploy fails on a stale lockfile).
2. Local end-to-end request: RSS under ~200 MB, total under ~8 s.
3. `python -m pytest`.
4. `fastapi deploy`.
5. Probe `/` then `/adaptive-quiz` twice; expect 200 both times.

## 5. Expected outcome

| Metric | Before | After |
|---|---|---|
| Cold quiz request | crash (502) | ~2-4 s |
| Warm quiz request | n/a | ~5-6 s (Groq-bound) |
| Resident memory | ~590 MB | ~120-180 MB |
| Container boot | ~10 s | ~2-3 s |

## 6. Notes

- Python must stay pinned to `==3.14.*`: `torch` and `onnxruntime` both ship
  cp314 wheels and neither ships cp315.
- Groq and Pinecone credentials are set in the FastAPI Cloud dashboard; `.env`
  is gitignored and never uploaded.
- The in-memory profile store is still process-local (AGENTS.md 6.11). Passing
  `competency_band` in the request body avoids cross-instance 404s.

---

## 7. Second bottleneck: Groq model latency

After the 502s were fixed the endpoint returned 200, but latency ranged from 2.4 s
to beyond 30 s. The container was healthy (`GET /` answered in 321 ms right after a
slow quiz call), so the variance was upstream.

Direct measurement of the same prompt, 4 sequential calls:

| Model | Time |
|---|---|
| `qwen/qwen3.8-27b` (previous default) | 48 s, 60 s, 56 s, 50 s |
| `qwen/qwen3.8-27b` | 18 s |
| `openai/gpt-oss-20b`, `reasoning_effort=low` | **1.1 – 1.8 s** |
| `openai/gpt-oss-120b`, `reasoning_effort=low` | 1.6 – 1.8 s |

All four candidates produced output that passed `validate_quiz` for BE, ME and EE.
The default is now `openai/gpt-oss-20b` with `reasoning_effort=low`.

Client hardening:

- `GROQ_TIMEOUT=12` and `max_retries=0`. The SDK default was `max_retries=2`, so a
  stalled call could burn minutes in backoff before reaching the fallback.
- `RateLimitError`, `APITimeoutError` and `APIConnectionError` now break the retry loop
  immediately; only schema/validation failures are retried. Two 20 s attempts could
  otherwise total 40 s and trip the gateway.
- The free tier allows **8000 tokens per minute**, and one quiz is ~2,400 tokens, so
  roughly 3 LLM-backed quizzes per minute; beyond that the endpoint serves the
  deterministic fallback bank in about a second instead of waiting out a doomed retry.

## 8. Results

Local, deployment-shaped venv (base dependencies only, torch absent):

| Metric | Before | After |
|---|---|---|
| Resident memory | 590 MB | **83 MB** (peak 89 MB) |
| `import main` | 3.0 s | 2.3 s |
| Cold retrieval | 60.6 s | 4.3 s (Pinecone connect) |
| Warm retrieval | 0.38 s | 0.29 s |
| Quiz generation | n/a | 0.7 – 1.8 s |

Production probe after deploy:

| Request | Before | After |
|---|---|---|
| `GET /` | 200, 1.1 s | 200, 320 ms warm |
| `GET /teacher/bands` | 200, 10.2 s | 200, 361 ms |
| `POST /adaptive-quiz` | **502, container killed** | **200, 1.1–1.4 s** |
| Container survives the call | no | yes |
| Fallback path (TPM exhausted) | n/a | 200, ~0.4 s |

Six consecutive production quizzes across BE/AE/ME/EE all returned 200 with the
correct question counts (4/5/5/6) in 0.4–1.4 s. One `GET /` returned a transient 503
during the deploy transition and recovered on the next request.

Remaining known limits:

- Groq free tier: 8000 TPM ≈ 3 LLM-backed quizzes per minute, then the deterministic
  fallback bank serves instead (still a valid, band-correct quiz).
- The in-memory profile store is process-local, so profile-scoped calls can 404 across
  autoscaled instances. Send `competency_band` in the body until it is persisted.

Vector parity was verified before switching: the worst cosine similarity between the
cached vectors and a freshly computed `sentence-transformers` embedding was
0.9999997 (float32 quantisation only).
