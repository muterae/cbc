# AGENTS.md — System Specification & Agent Architecture

This document defines the architecture, agentic components, data flows, learner
lifecycle, and development protocols for the **CBC Grade 3 AI-Driven Learning Companion**.

---

## 1. System Vision & Architecture

The system delivers automated, curriculum-grounded, adaptive learning for Grade 3
Mathematics under Kenya's Competency-Based Curriculum (CBC / KICD standard). It operates
under a **hybrid intelligence paradigm**:

1. **Deterministic / Predictive Layer (ML):** Classifies a learner into a CBC competency
   band from profile and activity data in under 5 ms.
2. **Context Retrieval Layer (RAG):** Fetches grounded curriculum outcomes, lesson
   activities and assessment rubrics from vector storage.
3. **Generative / Evaluator Layer (LLM):** Synthesises structured, pedagogically bounded
   quizzes and diagnostic summaries for the predicted instructional level.
4. **Learner Lifecycle Layer:** Onboards learners, logs every quiz response, measures
   performance, and reconciles predicted bands against termly exam results.

The lifecycle layer is what makes the system more than a one-off classifier: it supplies
the telemetry the predictor needs today and the labelled data it will need tomorrow.

### Component Topology

```
[Teacher / School] ──CSV profile import──┐
                                         ▼
[Kotlin Mobile Client] ──login, quiz events──> [FastAPI Server Engine]
        ▲                                        ├── [Event Logger & Performance Store]
        │                                        ├── [Predictive Classifier Agent]
        │                                        ├── [Curriculum Retrieval Agent]
        │                                        └── [Adaptive Synthesis Agent]
        │                                                │
        └────────── quiz + progress view ────────────────┘

[Teacher Dashboard] <── class overview, learner history, predicted vs exam band
```

---

## 2. Learner Lifecycle & Onboarding

### 2.1 Field sensitivity tiers

Profile fields are grouped by sensitivity, not by model importance. Only the low tier is
required; everything else can be declined and stored as `Unknown`.

| Tier | Fields | Handling |
|---|---|---|
| **Required / low** | `StudentID`, `Name`, `Class`, `Term`, `Attendance`, `Previous_Scores`, `Hours_Studied`, `School_Type`, `Teacher_Quality`, `Extracurricular_Activities` | Needed to run. Attendance and scores come from school records |
| **Useful / moderate** | `Access_to_Resources`, `Internet_Access`, `Parental_Involvement`, `Motivation_Level`, `Tutoring_Sessions`, `Sleep_Hours`, `Physical_Activity`, `Peer_Influence` | One short survey. "Prefer not to say" is allowed |
| **Sensitive** | `Family_Income`, `Learning_Disabilities`, `Parental_Education_Level`, `Distance_from_Home`, `Gender` | Optional. Explicit consent required. Stored as `Unknown` if declined |

Unseen categories, including `Unknown`, are ignored by the encoder
(`handle_unknown="ignore"`), and every imputed field is flagged so downstream analysis can
distinguish measured from assumed values.

### 2.2 Term-start import

1. School admin creates the term and classes.
2. Teacher downloads a CSV template with one row per learner.
3. Import validates unique `StudentID`, existing class, numeric ranges and categorical
   vocabulary. Invalid rows are quarantined with a report, not silently dropped.
4. Consent is captured for sensitive fields; declined fields are stored as `Unknown`.
5. Profiles are written with `source`, `term`, `survey_version` and `imputed_fields`.

### 2.3 Mid-term joiners

A learner who joins halfway through needs only `StudentID`, `Name` and `Class`.

- Numeric fields take the **class median** (falling back to school, then global).
- Categorical fields take `Unknown`, never the class mode.
- Every imputed field is flagged.
- The placement quiz replaces the median guess with real evidence on day one.

### 2.4 First login: fixed placement quiz

Every learner receives the same short placement quiz: 10–15 items spanning all four bands
and the main sub-strands. It is **not adaptive**. It provides:

- the first performance signal;
- a baseline for measuring progress;
- anchor items that are comparable across learners.

The band stays **provisional** until at least two sessions and roughly 20 answered
questions exist. The teacher sees "provisional" explicitly.

**Current implementation:** 12 items, 3 per band, generated once from RAG excerpts and
committed at `generator/output/intro_quiz.json`. The server serves the quiz without
`correct_answer` or `hint`, scores submissions, and stores the provisional band. The rule
is the highest band with at least 2 of 3 correct; otherwise BE. Regenerate the snapshot
with `python -m services.intro_quiz` and bump `INTRO_QUIZ_VERSION` when the prompt or item
count changes.

### 2.5 Weekly adaptation vs termly reporting

Two different things must not be conflated:

| Output | Cadence | Source | Purpose |
|---|---|---|---|
| **Instructional level** | Weekly (or every few sessions) | Rolling mastery from quiz responses | Chooses the difficulty of the next quiz |
| **Reported band** | Termly | End-of-term exam score, fixed cut points | Teacher report, parent communication |
| **Predicted band** | Per session | Classifier + activity features | Compared with the termly band at term end |

The reported band is **never** computed from quiz activity. The end-of-term exam score is
the only termly truth. Quiz activity may adapt difficulty within the term, but it does not
redefine the report card.

### 2.6 Performance measurement

The performance score is intentionally conservative:

1. **Correctness dominates.** First-attempt correctness is the primary signal.
2. **Difficulty weights the result.** A correct Exceeding item counts more than a correct
   Below item.
3. **Hints are support-seeking, not cheating.** Hint use is logged and may reduce the
   mastery estimate slightly, but it is never presented to the child as a punishment.
4. **Speed is diagnostic, not scored.** Very fast answers (under ~3 s) are flagged as
   possible guessing; very slow answers (many minutes) are flagged as interruption. Neither
   changes the score directly.
5. **Practice and assessment are separate.** Only placement and assessment sessions feed
   the band estimate. Practice sessions feed mastery and feature building.

A workable first formula:

```
question_score = is_correct × difficulty_weight
session_score  = mean(question_score) with hint use recorded
mastery        = exponential moving average of session scores
```

Scores are normalised to 0–100 so they can replace `Previous_Scores` without rescaling.

### 2.7 Event logging and null policy

Every session writes append-only events:

- `student_id`, `session_id`, `timestamp`, `session_type` (placement / practice / assessment)
- predicted band, instructional level, model version, feature snapshot
- `strand`, `sub_strand`, `skill_key`, question band
- `question_id`, correct answer, chosen answer, `is_correct`
- hints used, attempts, response time, skipped flag
- later: teacher band or exam score, as the training label

Null policy:

- Missing values are stored as `NULL`; they are never silently overwritten at rest.
- Imputation happens at feature-build time and is recorded in `imputed_fields`.
- Aggregate queries tolerate missing fields explicitly rather than dropping rows.
- As traffic grows, daily and weekly aggregates are precomputed; raw events are never
  scanned for every dashboard request.

---

## 3. Agent Roles & Specifications

### Agent 1: The Predictive Classifier (Telemetry Evaluator)

* **Type:** Supervised tabular ensemble (`XGBClassifier` inside a
  `scikit-learn.pipeline.Pipeline`).
* **Runtime:** In-memory on CPU within the FastAPI process lifespan.
* **Latency profile:** under 5 ms.
* **Artifact:** `predictor/cbc_predictor_bundle.pkl`.

#### Input schema (current model)

The production model is trained on the 19 columns of the proxy dataset:

| Numeric | Categorical |
|---|---|
| `Hours_Studied` | `Parental_Involvement` |
| `Attendance` | `Access_to_Resources` |
| `Sleep_Hours` | `Extracurricular_Activities` |
| `Previous_Scores` | `Motivation_Level` |
| `Tutoring_Sessions` | `Internet_Access` |
| `Physical_Activity` | `Family_Income` |
| | `Teacher_Quality` |
| | `School_Type` |
| | `Peer_Influence` |
| | `Learning_Disabilities` |
| | `Parental_Education_Level` |
| | `Distance_from_Home` |
| | `Gender` |

Planned quiz-derived features, added after enough real data exists: rolling accuracy over
7 and 30 days, hint rate, median normalised response time, completion rate, mastery per
strand, and improvement trend.

#### Internal pipeline

1. `SimpleImputer(strategy="median")` + `StandardScaler()` for numeric features.
2. `SimpleImputer(strategy="most_frequent")` + `OneHotEncoder(handle_unknown="ignore")`
   for categorical features.
3. `XGBClassifier(n_estimators=120, max_depth=5, learning_rate=0.08, eval_metric="mlogloss")`.
4. Output decoded through `LabelEncoder.inverse_transform` to produce the CBC band.

#### Target output bands

* `Below Expectation (BE)`
* `Approaching Expectation (AE)`
* `Meeting Expectation (ME)`
* `Exceeding Expectation (EE)`

The proxy model defines bands as quartiles of `Exam_Score` (cut points 65 / 67 / 69). In
live use the band comes from the end-of-term exam using fixed, school-agreed cut points.

#### Cold start

Before quiz history exists, the classifier produces a **provisional** band from the profile
alone. Confidence is reported alongside the band, and the placement quiz replaces the
profile guess with evidence.

---

### Agent 2: The Curriculum Retrieval Agent (RAG Grounding)

* **Type:** Dense semantic retriever over a vector index.
* **Storage:** Pinecone serverless index (`cbc-curriculum-rag`, AWS `us-east-1`).
* **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, cosine).
* **Runtime:** query embeddings are **precomputed**, not computed in the API process.
  The query string depends only on `(strand, sub_strand, band)`, and the vocabulary is
  fixed (3 strands, 14 sub-strands, 4 bands), so `generator/build_query_vectors.py`
  embeds all 72 reachable strings once into `services/query_vectors.json` (152 KB).
  `retriever.load_query_vectors()` reads that file at startup. This keeps
  `sentence-transformers` and `torch` out of the deployed image, where the import
  alone cost ~413 MB and ~37 s and caused the container to be OOM-killed (see
  `OPTIMIZATION.md`).
* **Status:** corpus built; **149 lesson vectors** embedded 2026-11-09.

#### Corpus

KICD Grade 3 Mathematics Teacher's Guide: 257 pages, 267,283 extracted characters,
3 terms, 3 strands, 14 sub-strands. Grade 2 is excluded because the only Grade 2 document
is a scan with no text layer.

#### Ingestion rules

* One chunk per lesson (149 lessons), plus the sub-strand preamble.
* Answer keys are emitted with `section="answers"` and `indexable=false`; they are never
  embedded or retrieved.
* `embedding_text` is capped under 1,000 characters because MiniLM truncates near 256
  tokens; the full `text` is retained in metadata for the prompt.
* Metadata: `chunk_id`, `grade`, `subject`, `term`, `strand`, `sub_strand`, `week`,
  `lesson`, `lesson_title`, `page_start`, `page_end`, `section`, `indexable`,
  `char_count`, `text`.
* Output: `generator/output/teacher_guide_chunks.jsonl` (293 chunks: 149 lessons +
  144 answer keys).

#### Retrieval protocol

```python
query = (
    f"Grade 3 Mathematics strand: {strand}, "
    f"sub-strand: {sub_strand}, assessment level: {band}"
)
# vector = services/query_vectors.json[query]   <- precomputed, no model load
# Top-K (default 3) with a sub_strand filter and indexable=true
```

`build_query` normalises the band, so `"ME"`, `"meeting-expectation"` and
`"Meeting Expectation"` all map to the same cached key. A cache miss is not an error:
the retriever logs it and returns static curriculum guidance. After adding a strand or
sub-strand to `services/curriculum.py`, regenerate the table with
`python generator/build_query_vectors.py`.

A sub-strand filter is mandatory: Numbers has 102 lessons against 7 for Geometry, so
pure similarity search is dominated by arithmetic.

---

### Agent 3: The Adaptive Synthesis Agent (Generative Assessment)

* **Type:** Hosted high-throughput LLM via Groq Cloud (`openai/gpt-oss-20b` by
  default, overridable with `GROQ_MODEL`).
* **Execution mode:** Few-shot prompt conditioning with forced JSON mode
  (`response_format={"type": "json_object"}`).
* **Latency budget:** `GROQ_REASONING_EFFORT=low` (default), a 12 s client timeout and
  `max_retries=0`. Rate limits, timeouts and connection errors are **not** retried — the
  endpoint falls straight through to the deterministic fallback bank, so a request cannot
  exceed roughly 12 s on the LLM leg. Only schema/validation failures are retried.
  The previous default model (`qwen/qwen3.8-27b`) took 18–60 s for the same prompt and
  overran the platform gateway timeout.
* **Temperature:** `0.3` – `0.4`, prioritising curriculum fidelity over variation.

#### Pedagogical difficulty mapping

* **Below Expectation (BE):** Concrete counting, visual cues, at most 12 words per
  question, step-by-step physical hints (counters, sticks).
* **Approaching Expectation (AE):** Single-step arithmetic, familiar Kenyan realia
  (shillings, mangoes, sukuma wiki), rule-reminder hints.
* **Meeting Expectation (ME):** Standard KICD end-of-sub-strand tasks, one- and two-step
  word problems, self-checking hints.
* **Exceeding Expectation (EE):** Inverse reasoning (`□ + 6 = 15`), missing-operator
  problems, comparison and critical-thinking prompts.

Band-global question counts: BE 4, AE 5, ME 5, EE 6. Regrouping is forbidden for BE and AE
and allowed for ME and EE.

#### Contract payload (JSON output)

```json
{
  "strand": "Numbers - Addition",
  "competency_band": "Approaching Expectation",
  "questions": [
    {
      "question_number": 1,
      "question_text": "Amina has 12 oranges. Juma gives her 5 more oranges. How many oranges does Amina have altogether?",
      "options": ["A) 15", "B) 16", "C) 17", "D) 18"],
      "correct_answer": "C) 17",
      "hint": "Count 5 steps forward starting from 12.",
      "pedagogical_objective": "Reinforce 2-digit plus 1-digit addition without regrouping."
    }
  ],
  "teacher_insight_summary": "Learner is practicing basic single-step word problems grounded in practical realia."
}
```

---

## 4. Communication Protocols & APIs

### Onboarding endpoints

- `GET /api/v1/intro-quiz` — the fixed 12-item placement quiz. The public payload has
  `quiz_id`, `version`, `title`, `question_count`, `generated_at`, `source` and
  `questions`. Each question has `question_number`, `question_text`, `options`, `band`,
  `strand`, `sub_strand` and `pedagogical_objective`; answers and hints are withheld.
- `POST /api/v1/profiles` — create or update a learner profile. Returns the stored
  `StudentProfile`.
- `GET /api/v1/profiles/{student_id}` — read a profile; 404 for unknown IDs.
- `POST /api/v1/profiles/{student_id}/placement` — score a placement submission:

  ```json
  {
    "quiz_id": "intro-v1",
    "answers": [
      {"question_number": 1, "selected_option": "C) 4"}
    ]
  }
  ```

  The server validates the quiz version and every option, returns the per-band breakdown
  and stores the provisional band. Re-submitting the same quiz version is idempotent; a
  different version returns 409.

### Primary endpoint: `POST /api/v1/adaptive-quiz`

#### Request payload

```json
{
  "student_id": "std_ke_09823",
  "strand": "Addition",
  "session_type": "practice"
}
```

The profile is stored server-side from the term import; it is not re-sent on every
request.

**Current implementation:** the endpoint is live. It reads `competency_band` from the
stored profile, so the mobile client does not send it. An optional `competency_band`
field remains for tests/admin overrides. An unknown profile returns 404; a profile
without a completed placement returns 409.

#### Processing sequence

1. Validate the request and resolve the learner's role and class.
2. Load the stored profile and the latest performance snapshot.
3. Predict the band prior with the classifier, or reuse the provisional band.
4. Apply the weekly instructional level derived from rolling mastery.
5. Retrieve curriculum chunks for the strand and sub-strand (Top-3, `indexable=true`).
6. Build the prompt from chunks, band rules and few-shot examples.
7. Call Groq in JSON mode; validate against the response schema.
8. Persist the prediction, feature snapshot, model version and generated quiz.
9. Return the validated payload to the client.

### Planned endpoints

- `POST /api/v1/sessions` — open or close a quiz session.
- `POST /api/v1/responses` — log a single answered question.
- `POST /api/v1/teacher/import` — CSV profile import with validation report.
- `POST /api/v1/teacher/exam-scores` — termly exam import; sets the reported band.
- `GET /api/v1/teacher/classes/{class_id}` — class and learner views.
- `GET /api/v1/teacher/bands` — list every band playbook.
- `GET /api/v1/teacher/bands/{band}` — one band playbook for teacher views.

---

## 5. Development & Operation Workflows

### Environment variables (`.env`)

```bash
PINECONE_API_KEY="pcsk_..."
GROQ_API_KEY="gsk_..."
GROQ_MODEL="openai/gpt-oss-20b"        # optional override
GROQ_REASONING_EFFORT="low"            # set "" for non-reasoning models
GROQ_TIMEOUT="20"                      # seconds, per attempt
```

### Commands

```bash
# Predictor
python predictor/train_model.py        # train XGBoost, write bundle + metrics.json
python predictor/compare_models.py     # model comparison -> model_comparison.json

# Corpus
python generator/ingest_documents.py   # extract PDFs to output/*.txt
python generator/probe_structure.py    # map terms, strands, sub-strands
# Lesson chunking output already exists at generator/output/teacher_guide_chunks.jsonl;
# the chunker script is not currently in the working tree.

# Retrieval
python generator/embed_curriculum.py --dry-run
python generator/embed_curriculum.py
python generator/test_retrieval.py

# Precomputed query vectors (required after any change to services/curriculum.py)
python generator/build_query_vectors.py

# Fixed placement quiz (writes generator/output/intro_quiz.json)
python -m services.intro_quiz

# Server and tests
uv sync --extra dev                   # dev extra carries torch, xgboost, pytest
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
python -m pytest
```

The deployed image installs only the base dependencies (`fastapi[standard]`, `groq`,
`pinecone`, `pydantic`, `python-dotenv`). Everything in the `dev` extra is offline
tooling: training, ingestion and embedding generation.

---

## 6. Guardrails & Failure Modes

1. **Vector DB fallback:** if Pinecone times out or is rate-limited, fall back to a static
   in-memory map of Grade 3 KICD core competencies for the requested strand.
2. **Label decoding:** always decode predictions with `LabelEncoder.inverse_transform`;
   never use a hand-written dictionary.
3. **JSON schema enforcement:** Groq must return JSON mode. If validation fails, return a
   deterministic fallback quiz for the strand rather than a 500 to the client.
4. **PII isolation:** `StudentID`, `Name` and other identifiers never enter the training
   matrix.
5. **No silent nulls:** missing values are stored as `NULL`, imputed at feature-build time,
   and flagged. Silent imputation is forbidden.
6. **Feedback-loop separation:** practice and assessment sessions are distinct. Adaptive
   practice must not be used as evidence for the reported band, or easy questions will
   inflate the estimate.
7. **Exam score is the only termly truth:** the reported band comes from the end-of-term
   exam, never from the model's own activity estimate.
8. **Provisional bands:** a learner without a placement quiz or sufficient evidence is
   labelled provisional; the system must not present a settled band from imputed data.
9. **Consent and sensitive fields:** sensitive fields are optional, consent-gated, and
   stored as `Unknown` when declined. They are never required to use the system.
10. **Model versioning:** every prediction stores the model version and feature snapshot.
    Retraining uses a temporal split and enters shadow mode before replacing the live model.
11. **In-memory profiles are temporary:** the simulation store is process-local, lost on
    restart, and safe only with a single worker. It must not hold real learner data; replace
    it with a persistent `ProfileStore` before production.
