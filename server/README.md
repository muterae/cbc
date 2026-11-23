# CBC AI Learning Companion

Backend for an adaptive Grade 3 Mathematics quiz generator, grounded in Kenya's
Competency-Based Curriculum (CBC).

The teacher imports learner profiles once per term. The child's app sends quiz activity.
The system places the learner in a CBC band, fetches the right KICD lesson, and asks a
language model to write a quiz at that level.

```
profile + quiz activity ──> [ predictor ] ──> band (BE / AE / ME / EE)
                                     │
                          strand + band
                                     ▼
                        [ curriculum retrieval ] ──> KICD lesson
                                     │
                                     ▼
                        [ quiz generation ] ──> validated JSON quiz
```

---

## Current state

Status as of November 2026.

| Part | What it does | Status |
|---|---|---|
| **Predictor** | Places a learner in one of four competency bands | **Working** |
| **Curriculum corpus** | Extracts, maps and chunks the Grade 3 Teacher's Guide | **Working** |
| **Embeddings + retrieval** | Searches the corpus for the right lesson | **Working** — 149 vectors in `cbc-curriculum-rag` |
| **Band playbook** | Maps BE/AE/ME/EE to item counts and difficulty | **Working** — tested, teacher endpoint live |
| **Quiz generation** | Prompts the LLM and validates its JSON | **Working** — Groq JSON mode + fallback |
| **Onboarding & lifecycle** | Profiles, placement quiz, weekly adaptation, termly band | **Partial** — in-memory profiles + fixed placement quiz |
| **API** | Serves the mobile client | **Working** — profiles, placement, adaptive quiz, teacher bands |
| **Evaluation** | Measures retrieval and question quality | **Not started** |

The server path is **connected end to end**: profile → fixed placement quiz → provisional
band → curriculum retrieval → band playbook → LLM generation → validation → fallback.
Profiles are in memory for the simulation build; the predictor is not wired into the
endpoint yet. The mobile app still uses its local fallback quiz.

### What works today

- **Predictor:** XGBoost trained on 6,607 learners, 19 features.
  Cross-validated accuracy **0.747 ± 0.015**, holdout **0.742** (random guessing: 0.250).
- **Corpus:** 257 pages extracted, 3 terms, 14 sub-strands, **293 chunks**
  (149 complete lessons + 144 answer keys). Structure validation passes 41/41.
  Chunk schema and provenance: [generator/CHUNKING.md](generator/CHUNKING.md).
- **Retrieval:** MiniLM embeddings in `cbc-curriculum-rag` (384d, cosine, **149 vectors**).
  Six band-shaped queries pass with a mandatory sub-strand filter; run details are in
  `generator/output/embedding_manifest.json`.
- **Band playbook:** `services/band_playbook.py` defines the BE/AE/ME/EE difficulty
  ladder, item counts, word caps, hint style and example items. Human view:
  `docs/band-playbook.md`.
- **Fixed placement quiz:** `GET /api/v1/intro-quiz` serves the same 12-item quiz to every
  learner, 3 items per band, spanning Numbers, Measurement and Geometry. RAG grounds each
  band and Groq generates it once; the validated snapshot is
  `generator/output/intro_quiz.json`. Regenerate with `python -m services.intro_quiz`.
- **Profiles:** `POST /api/v1/profiles` and `GET /api/v1/profiles/{student_id}`. The store
  is in memory and seeded with two demo learners.
- **Placement scoring:** `POST /api/v1/profiles/{student_id}/placement`. The server scores
  the quiz, stores the provisional band and returns the per-band breakdown. The rule is the
  highest band with at least 2 of 3 correct; otherwise BE.
- **Adaptive quiz:** `POST /api/v1/adaptive-quiz` reads the band from the stored profile,
  retrieves top-3 lessons, prompts Groq (`openai/gpt-oss-20b`) in JSON mode, validates
  against the band playbook, retries once, then returns a deterministic fallback quiz if
  generation still fails. The optional `competency_band` field remains for tests/admin.
- **Teacher band API:**
  `GET /api/v1/teacher/bands` and `GET /api/v1/teacher/bands/{band}`.
- **Not yet:** persistent profile storage, predictor integration, event logging, weekly
  mastery updates and evaluation.

> **In-memory caveat:** profiles disappear when the server restarts and are process-local.
> Run a single worker for demos. Do not use this store for real learner data.

### API

Onboarding flow:

```bash
GET /api/v1/intro-quiz

POST /api/v1/profiles
{
  "student_id": "std_001",
  "name": "Amina",
  "grade": "Grade 3",
  "class_name": "3A",
  "term": "Term 1"
}

POST /api/v1/profiles/std_001/placement
{
  "quiz_id": "intro-v1",
  "answers": [
    {"question_number": 1, "selected_option": "C) 4"}
  ]
}
```

`GET /api/v1/intro-quiz` omits `correct_answer` and `hint`; the server keeps the answer
key. Placement requires exactly one valid answer per question. Submitting the same quiz
version again is idempotent.

Adaptive practice reads the stored band:

```bash
POST /api/v1/adaptive-quiz
{
  "student_id": "std_ke_09823",
  "strand": "Addition",
  "session_type": "practice"
}
```

`strand` accepts a top-level strand, a sub-strand (`Addition`), or
`Numbers - Addition`. `competency_band` is optional and only for tests/admin; normally the
band comes from the profile. A missing profile returns 404 and an incomplete placement
returns 409. The response is the quiz payload in [AGENTS.md](AGENTS.md) §3: `strand`,
`competency_band`, `questions`, `teacher_insight_summary`.

Teacher views can read the band rules directly:

```bash
GET /api/v1/teacher/bands
GET /api/v1/teacher/bands/AE
```

---

## Onboarding and learner lifecycle

A learner is onboarded once per term. The flow is short for the child and front-loaded for
the teacher.

### 1. Term start: profile import

The teacher imports a CSV, one row per learner. Fields are grouped by sensitivity:

| Sensitivity | Fields | Handling |
|---|---|---|
| **Required / low** | student ID, name, class, term, attendance, previous score, study hours, school type, teacher quality, extracurricular activities | Needed to run; attendance and scores come from school records |
| **Useful / moderate** | access to resources, internet access, parental involvement, motivation, tutoring, sleep, physical activity, peer influence | One short survey; "prefer not to say" is allowed |
| **Sensitive** | family income, learning disabilities, parental education, distance from home, gender | Optional; explicit consent; stored as `Unknown` if declined |

The import validates IDs, duplicates and impossible values before writing anything.
Missing values are stored as `NULL` with a source flag; they are never silently filled.

The simulation build uses `POST /api/v1/profiles` and an in-memory store instead of CSV
import. Profiles are seeded with Amina (`std_ke_09823`, AE) and Brian
(`std_ke_09824`, ME).

### 2. First login: fixed placement quiz

Every learner takes the same short placement quiz: 12 questions, 3 per band, spanning the
main sub-strands. It produces the first real performance signal and a baseline for
progress. The server scores it and marks the band **provisional**. The current placement
rule is the highest band with at least 2 of 3 correct, otherwise BE.

The generated question bank is cached and committed at
`generator/output/intro_quiz.json`. The fixed quiz stays identical across restarts and
learners; changing the prompt or item count requires regenerating the snapshot and
bumping `INTRO_QUIZ_VERSION`.

### 3. During the term: weekly adaptation

The **instructional level** — the difficulty of the next quiz — is recalculated weekly from
rolling mastery. Correctness counts most, question difficulty weights the result, and hints
and speed are logged but never used as punishments. The **reported band** does not change
mid-term.

### 4. Term end: the exam score sets the band

Only the end-of-term exam score sets the termly band, using fixed cut points. The system
compares that band with its own predictions and stores both. That comparison is the
evaluation, and the exam band becomes the label for the next retraining round.

### 5. Mid-term joiners

A learner who joins halfway through needs only an ID, name and class. Numeric fields take
the class median, categorical fields take `Unknown`, and every imputed field is flagged.
The placement quiz replaces the guess with real evidence on day one.

### What the learner and teacher see

- **Learner:** log in, take a quiz, view progress — no band labels.
- **Teacher:** class overview, per-learner history, provisional versus stable band, and the
  predicted-versus-exam comparison at term end.

As the event log grows, daily and weekly aggregates are precomputed, and queries tolerate
missing fields explicitly rather than dropping rows.

---

## Repository layout

| Path | Contents |
|---|---|
| `predictor/` | Dataset, training script, model artifact, evaluation and reports |
| `generator/` | PDF ingestion, structure probe, embeddings; chunker and intro quiz snapshot |
| `services/` | Band playbook, quiz generation, fallback, intro quiz and profile store |
| `routers/` | HTTP routes (profiles, placement, adaptive quiz, teacher bands) |
| `main.py` | FastAPI entry point |
| `deliverables/` | Assignment plans and submissions |

---

## Documentation

**Predictor**
- [README](predictor/README.md) — usage, artifacts, how to decode predictions
- [REPORT](predictor/REPORT.md) — dataset, cleaning, cross-validation, model comparison
- [REGRESSION](predictor/REGRESSION.md) — the linear and logistic baselines
- [PRESENTATION](predictor/PRESENTATION.md) — plain-language walkthrough and numbers to quote

**Curriculum layer**
- [README](generator/README.md) — extraction and chunking pipeline
- [REPORT](generator/REPORT.md) — corpus audit, structure analysis, chunk statistics
- [PRESENTATION](generator/PRESENTATION.md) — plain-language walkthrough and remaining work

**Project**
- [AGENTS.md](AGENTS.md) — architecture, agent roles and guardrails
- [Deliverable 2 plan](deliverables/deliverable2.md) — CAT 2 scope and status

---

## Scope and limitations

- The project is **Grade 3 Mathematics**. Grade 2 was dropped because the only Grade 2
  document is a scan with no text layer.
- The predictor's dataset is a public Kaggle dataset, not Kenyan CBC telemetry. It is a
  proxy, and the bands are cohort-relative quartiles, not official KICD descriptors.
- The corpus is the KICD Teacher's Guide, but diagrams and stacked fractions survive only
  as linearised text.
- Retrieval smoke tests pass, but generated question quality is not yet evaluated against
  a human-reviewed answer key.
- The profile store is in memory: process-local, lost on restart, and only safe with a
  single worker. It is a simulation placeholder, not a production learner record.
- The placement snapshot is committed for reproducibility. Regenerate it only when the
  prompt, targets or item count change, and bump `INTRO_QUIZ_VERSION`.
