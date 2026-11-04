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

Status as of October 2026.

| Part | What it does | Status |
|---|---|---|
| **Predictor** | Places a learner in one of four competency bands | **Working** |
| **Curriculum corpus** | Extracts, maps and chunks the Grade 3 Teacher's Guide | **Working** |
| **Embeddings + retrieval** | Searches the corpus for the right lesson | **In progress** — 0 vectors yet |
| **Quiz generation** | Prompts the LLM and validates its JSON | **Not started** — stubs only |
| **Onboarding & lifecycle** | Profiles, placement quiz, weekly adaptation, termly band | **Designed** — not implemented |
| **API** | Serves the mobile client | **Stub** |
| **Evaluation** | Measures retrieval and question quality | **Not started** |

The end-to-end path is **not connected yet**. The predictor works on its own, and the
curriculum corpus is built and validated, but nothing joins them to a live quiz endpoint.

### What works today

- **Predictor:** XGBoost trained on 6,607 learners, 19 features.
  Cross-validated accuracy **0.747 ± 0.015**, holdout **0.742** (random guessing: 0.250).
- **Corpus:** 257 pages extracted, 3 terms, 14 sub-strands, **293 chunks**
  (149 complete lessons + 144 answer keys). Structure validation passes 41/41.
- **Not yet:** embeddings, retrieval, the band playbook, quiz generation, API integration.

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

### 2. First login: fixed placement quiz

Every learner takes the same short placement quiz: 10–15 questions spanning all four bands
and the main sub-strands. It produces the first real performance signal and a baseline for
progress. Until it is done, the band is marked **provisional**.

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
| `generator/` | PDF ingestion, structure probe, lesson chunker, embedding scripts |
| `services/` | Quiz schema and generative-AI stubs |
| `main.py` | FastAPI entry point (currently two placeholder routes) |
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
- Retrieval has not been tested yet, so no claim is made about answer quality.
