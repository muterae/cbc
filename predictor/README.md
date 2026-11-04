# CBC Student Competency Predictor

Turns learner telemetry into one of four CBC competency bands (**BE / AE / ME / EE**).
The band is passed to the RAG + LLM layers, which choose Grade 3 KICD content difficulty.

**Full statistics, cleaning details, column list and model comparison: [REPORT.md](REPORT.md).**

---

## Dataset

Kaggle **Student Performance Factors** (`lainguyn123`): 6,607 learners, 19 features.

| Strongest signals | r with `Exam_Score` |
|---|---|
| `Attendance` | +0.581 |
| `Hours_Studied` | +0.446 |
| `Previous_Scores` | +0.175 |
| `Tutoring_Sessions` | +0.156 |

Bands are quartiles of `Exam_Score`; cut points are stored in the artifact.

---

## Results at a glance

| Model | CV accuracy |
|---|---|
| **XGBoost** | **0.747 ± 0.015** |
| Random Forest | 0.703 ± 0.015 |
| Decision Tree | 0.596 ± 0.011 |

Full breakdown in [REPORT.md §8](REPORT.md#8-model-comparison).

---

## Usage

```bash
python predictor/train_model.py      # train, cross-validate, write bundle + metrics.json
python predictor/compare_models.py   # model comparison -> model_comparison.json
python predictor/test_inference.py   # smoke-test three sample learners
python predictor/evaluate.py         # stats, correlations, CV, importances
```

| Artifact | Contents |
|---|---|
| `cbc_predictor_bundle.pkl` | Pipeline, label encoder, feature lists, band cut points, metrics |
| `metrics.json` | Same metrics as plain JSON |

---

## Decoding predictions

`LabelEncoder` sorts band names **alphabetically**, not by difficulty. Always decode with
the same encoder:

```python
band = artifact["label_encoder"].inverse_transform([idx])[0]
```

Never use a hand-written dictionary — that was the old bug, which silently swapped
BE↔AE and ME↔EE.

---

## Limitations

Not Kenyan, not CBC-specific, cohort-relative bands. See
[REPORT.md §10](REPORT.md#10-limitations) for the full list and the dataset search that
justifies the proxy choice.

---

## Experimental — not yet validated

Linear and logistic regression were tested as baselines and their full findings are recorded in [REGRESSION.md](REGRESSION.md); neither is part of the deployed model.
