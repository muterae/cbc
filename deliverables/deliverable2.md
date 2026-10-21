# Deliverable 2 (CAT 2) — Task Plan

**Course:** ICS 3202 Artificial Intelligence
**Deliverable:** Project Deliverable 2 (CAT 2) — ML Engine
**Window:** 19 Oct 2026 → 6 Nov 2026 (presentations 26 Oct – 6 Nov, all four classes mandatory)
**Submitted as:** `XGBoost_Base.ipynb` in public repo `SemProject_MLEngine`

---

## 0. Where the project stands

| Area | Status |
|---|---|
| Dataset | **Student Performance Factors** (Kaggle `lainguyn123`), 6,607 rows, 19 features |
| XGBoost classifier | Trained — CV accuracy **0.747 ± 0.015** |
| Label decoding | **Fixed** — single `LabelEncoder` used both ways |
| Cleaning + feature pipeline | Done (`predictor/train_model.py`) |
| Cross-validation | Done — stratified 5-fold |
| Smoke test | Done (`predictor/test_inference.py`, 3 learners) |
| Statistics script | Done (`predictor/evaluate.py`) |
| Notebook (`XGBoost_Base.ipynb`) | **Not started** |
| Model comparison | **Not started** |
| `SemProject_MLEngine` repo | **Not created** |
| RAG + LLM + API layer | Stubs only — outside CAT 2 marking |

CAT 2 grades the **ML workflow notebook**, not the server. The model is ready; the notebook is the remaining work.

---

## 1. Brief → task map

| Brief instruction | Marks | Task | Owner |
|---|---|---|---|
| 1. Identify ML approach + algorithm; add to shared spreadsheet | — | Row: classification, XGBoost + baselines | Team |
| 2. Notebook: cleaning from exploration to final dataset; ≥4 EDA observations | Notebook 8 | Notebook §4–§5 | Notebook lead |
| 3. Describe base model; apply validation (CV for classification) | Notebook 8 | Notebook §7–§9 | Model lead |
| 4. Other validation methods; build comparable models and compare | Notebook (final review) | Notebook §10–§11 | Model lead |
| 5. Present code plainly, no jargon | Presentation 12 | Rehearse each section | All |
| — Attendance all 4 classes, everyone present | Teamwork 10 | Calendar block | All |
| — Publish notebook, teammates fork | Submission gate | §4 below | Repo owner |

---

## 2. Predictor cleanup — completed

The work below is done and verified by running all three scripts.

### 2.1 Label decoding bug (fixed)
`LabelEncoder` sorts band names **alphabetically**, so the model's integers were
0=Approaching, 1=Below, 2=Exceeding, 3=Meeting. The old bundle decoded them with a
difficulty-ordered dictionary (0=Below, 1=Approaching, 2=Meeting, 3=Exceeding), which
swapped BE↔AE and ME↔EE with no error. Decoding is now:

```python
band = artifact["label_encoder"].inverse_transform([idx])[0]
```

- [x] Decode with `label_encoder.inverse_transform`
- [x] Delete `target_mapping`, `inv_target_mapping`, stale `label_mapping`
- [x] Store encoder + classes in the bundle and assert they match
- [x] Rewrite `test_inference.py` for the real schema
- [x] Delete `open_pkl.py`
- [x] Smoke test asserts the output is one of the four CBC bands

### 2.2 Dataset switch (fixed the no-signal problem)
The old dataset (`student-performance-predictions.csv`) had |r| < 0.05 for every feature
and scored 0.27 (random = 0.25). It was replaced with **Student Performance Factors**:

| | Old dataset | New dataset |
|---|---|---|
| Rows | 1,000 (960 usable) | 6,607 |
| Features | 7 | 19 |
| Target | `FinalGrade` 62–92 | `Exam_Score` 55–101 |
| Strongest correlation | 0.040 | **0.581** (Attendance) |
| CV accuracy | 0.27 | **0.747** |

### 2.3 Other fixes
- [x] Missing target was mapped to "Below Expectation" → now dropped
- [x] `Exam_Score = 101` clipped to 100
- [x] Categorical spelling normalised
- [x] Imputation, scaling and one-hot encoding kept inside the pipeline (no leakage)
- [x] Quartile band cut points stored in the artifact
- [x] Metadata saved: versions, date, cut points, row counts
- [x] `metrics.json` written for the notebook
- [x] README rewritten

### 2.4 Results to report in the notebook

| Metric | Value |
|---|---|
| 5-fold CV accuracy | 0.747 ± 0.015 |
| 5-fold CV macro F1 | 0.726 ± 0.016 |
| Holdout accuracy | 0.742 |
| Holdout macro F1 | 0.72 |
| Random baseline | 0.25 |

| Band | Precision | Recall | F1 |
|---|---|---|---|
| Below Expectation | 0.86 | 0.89 | 0.88 |
| Approaching Expectation | 0.59 | 0.60 | 0.59 |
| Meeting Expectation | 0.59 | 0.55 | 0.57 |
| Exceeding Expectation | 0.84 | 0.84 | 0.84 |

---

## 3. Notebook outline (`XGBoost_Base.ipynb`)

### 3.0 Framing (write this in §1)
The ML engine scores **general learner competency** from telemetry. It is not a Grade 2
model. Grade 2 content is supplied downstream by the RAG layer. State this in the intro
and again in Limitations.

1. Title, group members, problem statement, dataset source + licence
2. Setup and pinned imports
3. Load data: shape, dtypes, head
4. **EDA — at least 4 observations**, each with a chart and one sentence:
   - O1: `Exam_Score` distribution is narrow (55–101), which is why quartiles are used
   - O2: attendance vs score — strongest relationship (r = 0.58)
   - O3: hours studied vs score (r = 0.45)
   - O4: parental involvement / access to resources vs band
   - O5: missing values concentrated in 3 columns (235 cells)
   - O6: one impossible score (101) and no duplicates
5. **Cleaning log** — table: problem → action → rows affected
6. Target banding — quartiles, cut points, why not fixed 40/60/80
7. Preprocessing pipeline — `ColumnTransformer`, imputers, scaler, one-hot
8. Base model — XGBoost, hyperparameters, why chosen
9. **Validation** — stratified 5-fold CV, mean ± std, confusion matrix, per-class report,
   explain why preprocessing sits inside the pipeline
10. **Comparison models** — identical split and preprocessing, one loop:
    - Logistic Regression (simplest baseline)
    - Decision Tree (explainable baseline)
    - XGBoost (model of record)
11. Results table + discussion: XGBoost vs baselines, confusion between middle bands
12. Export bundle + inference snippet with correct decoding
13. Limitations and next steps (RAG + LLM quiz generation)

Checklist: markdown above every code block, no unexplained output, runs top-to-bottom on a clean kernel, no hardcoded paths.

---

## 4. Repo and submission

New, separate public repo. `cbc-server` stays untouched and is only linked.

- [ ] Create public repo `SemProject_MLEngine`
- [ ] Notebook at root: `XGBoost_Base.ipynb`
- [ ] `README.md`: problem, dataset, how to run, results table, link to `cbc-server`
- [ ] `requirements.txt` with pinned versions
- [ ] `.gitignore`: venv, `.env`, `*.pkl`, large PDFs
- [ ] Push before 6 Nov; every member forks; screenshots as evidence
- [ ] Notebook comments in the team's own words (brief warns against AI-generated text)

---

## 5. Roadmap after CAT 2 (not graded now)

1. `generator/embed_curriculum.py` — chunk `output.txt`, embed with MiniLM, upsert to Pinecone
2. `retriever.py` — query function, `load_dotenv()`, Top-3 retrieval, static fallback
3. `services/generative_ai.py` — band→difficulty prompt, Groq JSON mode, validation, fallback quiz
4. `main.py` — `lifespan` model load, `POST /api/v1/adaptive-quiz`, CORS
5. Deps: add `pinecone`, `sentence-transformers`, `openpyxl` to `pyproject.toml`
6. Fix Pydantic v1 `min_items` in `services/quiz.py`; add `question_number`, `pedagogical_objective`
7. Commit `AGENTS.md`, `generator/`, `deliverables/`

---

## 6. Definition of done (CAT 2)

- [x] Label decoding fixed and verified
- [x] Model trained, cross-validated, smoke-tested
- [x] Statistics generated (`metrics.json`)
- [ ] Notebook runs top-to-bottom with ≥4 EDA observations
- [ ] Cleaning log table
- [ ] CV + ≥3 comparison models in one results table
- [ ] Honest discussion of limitations
- [ ] Public `SemProject_MLEngine` repo with notebook, README, requirements
- [ ] All members forked and can explain their section
- [ ] Presentation rehearsed; all four classes attended

---

## 7. Decisions made

1. **Dataset** — Student Performance Factors (Kaggle `lainguyn123`). Real signal, schema close to app telemetry, no registration, reproducible via `kagglehub`.
2. **Framing** — engine predicts general competency; Grade 2 comes from the RAG layer.
3. **Model of record** — XGBoost (CV 0.747). Baselines must beat or approach it.
4. **Repo** — standalone public `SemProject_MLEngine`; `cbc-server` untouched.
5. **Comparison set** — Logistic Regression + Decision Tree (+ Random Forest if time). KNN dropped.
6. **Bands** — quartiles of `Exam_Score`, cut points stored in the artifact.
7. **Old dataset** — kept on disk at `predictor/data/student-performance-predictions.csv` for reference, no longer used.

## 8. Still open

- Group member names for the notebook title page
- Presentation date and who presents which section
- Whether to cite AHEAD (DataFirst, CC-BY 4.0) as a future African dataset in Limitations
