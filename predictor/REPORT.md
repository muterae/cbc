# Predictor Report — CBC Competency Classifier

All figures in this report were produced by `train_model.py` and `evaluate.py` on
21 October 2026. Random seed 42 throughout.

---

## 1. Objective

Classify a learner into one of four CBC competency bands — **BE, AE, ME, EE** — from
telemetry the mobile app can collect. The band is later used by the RAG layer to choose
Grade 2 KICD content difficulty. The model does not know about Grade 2; it scores general
competency.

---

## 2. Dataset

**Kaggle "Student Performance Factors"** (`lainguyn123/student-performance-factors`),
cached at `data/student-performance-factors.csv`.

| Property | Value |
|---|---|
| Rows | 6,607 |
| Columns | 20 (19 features + 1 target) |
| Duplicate rows | 0 |
| Missing cells | 235 in 3 columns |
| Target | `Exam_Score`, range 55–101 |

### 2.1 Columns

| Column | Type | Role | Notes |
|---|---|---|---|
| `Hours_Studied` | int | feature | weekly study hours |
| `Attendance` | int | feature | attendance rate, 60–100 |
| `Sleep_Hours` | int | feature | average nightly sleep |
| `Previous_Scores` | int | feature | past assessment average |
| `Tutoring_Sessions` | int | feature | sessions attended |
| `Physical_Activity` | int | feature | weekly activity |
| `Parental_Involvement` | Low/Medium/High | feature | |
| `Access_to_Resources` | Low/Medium/High | feature | |
| `Extracurricular_Activities` | Yes/No | feature | |
| `Motivation_Level` | Low/Medium/High | feature | |
| `Internet_Access` | Yes/No | feature | |
| `Family_Income` | Low/Medium/High | feature | |
| `Teacher_Quality` | Low/Medium/High | feature | 78 missing |
| `School_Type` | Public/Private | feature | |
| `Peer_Influence` | Positive/Neutral/Negative | feature | |
| `Learning_Disabilities` | Yes/No | feature | |
| `Parental_Education_Level` | High School/College/Postgraduate | feature | 90 missing |
| `Distance_from_Home` | Near/Moderate/Far | feature | 67 missing |
| `Gender` | Male/Female | feature | |
| `Exam_Score` | int | **target** | 55–101; one value clipped to 100 |

---

## 3. Cleaning

| Problem | Action | Rows affected |
|---|---|---|
| Missing target | Drop | 0 |
| Duplicate rows | Drop | 0 |
| `Exam_Score = 101` (impossible) | Clip to 100 | 1 |
| `Attendance > 100` | Clip to 0–100 | 0 |
| Category spelling | Trim, title-case | — |
| Missing features | Imputed inside the pipeline | 235 |

Missing cells: `Teacher_Quality` 78, `Parental_Education_Level` 90, `Distance_from_Home` 67.

No `StudentID` or `Name` column exists, so there is no identifier leakage to remove.

---

## 4. Target bands

`Exam_Score` is continuous and concentrated (mean 67.2, SD 3.9). Fixed 40/60/80 cut-offs
would leave classes empty, so bands are quartiles:

| Band | Cut point | Records |
|---|---|---|
| Below Expectation | < 65 | 2,131 |
| Approaching Expectation | 65 – 66 | 1,468 |
| Meeting Expectation | 67 – 68 | 1,383 |
| Exceeding Expectation | ≥ 69 | 1,625 |

The cut points are stored in the artifact, so inference reproduces the same definition.
The uneven counts come from tied integer scores at the boundaries.

---

## 5. Preprocessing

```
numeric    → SimpleImputer(median)      → StandardScaler
categorical → SimpleImputer(most_frequent) → OneHotEncoder(handle_unknown="ignore")
           → classifier
```

Everything sits inside one scikit-learn `Pipeline`. During cross-validation the
preprocessing is refitted on each training fold, so no information from the test fold
leaks into training.

---

## 6. Validation method

**Stratified 5-fold cross-validation** on all 6,607 rows: the data is split into five
equal folds; each fold is held out once while the model trains on the other four. The
score is the mean of the five runs, and `±` is their standard deviation (stability).
Stratified means each fold keeps the same band proportions.

A separate **80/20 holdout** (1,322 rows) is untouched during CV and used as a final
independent check.

---

## 7. XGBoost results

| Metric | Value |
|---|---|
| CV accuracy | **0.747 ± 0.015** |
| CV macro F1 | 0.726 ± 0.016 |
| Holdout accuracy | 0.742 |
| Holdout macro F1 | 0.72 |
| Random baseline (4 classes) | 0.25 |

### 7.1 Per-class performance (holdout)

| Band | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Below Expectation | 0.86 | 0.89 | 0.88 | 426 |
| Approaching Expectation | 0.59 | 0.60 | 0.59 | 294 |
| Meeting Expectation | 0.59 | 0.55 | 0.57 | 277 |
| Exceeding Expectation | 0.84 | 0.84 | 0.84 | 325 |

The extreme bands are learned well. The two middle bands are confused with each other
because their boundaries are one or two score points apart.

### 7.2 Correlations with `Exam_Score`

| Feature | r |
|---|---|
| `Attendance` | +0.581 |
| `Hours_Studied` | +0.446 |
| `Previous_Scores` | +0.175 |
| `Tutoring_Sessions` | +0.156 |
| `Physical_Activity` | +0.028 |
| `Sleep_Hours` | −0.017 |

### 7.3 Top model importances

| Feature | Importance |
|---|---|
| `Attendance` | 0.103 |
| `Hours_Studied` | 0.074 |
| `Access_to_Resources = High` | 0.050 |
| `Parental_Involvement = High` | 0.044 |
| `Parental_Involvement = Low` | 0.042 |

---

## 8. Model comparison

Identical preprocessing, identical folds, identical holdout split.

| Model | CV accuracy | CV macro F1 | Holdout accuracy | CV time |
|---|---|---|---|---|
| **Logistic Regression** | **0.950 ± 0.006** | **0.947 ± 0.006** | **0.945** | 1.8 s |
| XGBoost | 0.747 ± 0.015 | 0.726 ± 0.016 | 0.742 | 4.7 s |
| Random Forest | 0.703 ± 0.015 | 0.664 ± 0.018 | 0.708 | 5.4 s |
| Decision Tree | 0.600 ± 0.007 | 0.578 ± 0.008 | 0.590 | 0.7 s |

### 8.1 Step-by-step comparison procedure

1. Load and clean the data once.
2. Build the four bands once, with fixed cut points.
3. Encode the target once.
4. For each model: wrap the **same** preprocessor and the model in a `Pipeline`.
5. Run stratified 5-fold CV on all rows, scoring accuracy and macro F1.
6. Fit once on the 80% training split and score the 20% holdout.
7. Record mean, standard deviation, holdout score and run time.
8. Compare in one table.

### 8.2 Why Logistic Regression wins

The target is close to a linear function of the features:

```
Exam_Score ≈ 42.0 + 0.290 × Hours_Studied + 0.198 × Attendance + 0.048 × Previous_Scores
R² = 0.57 (3 features), 0.60 (all numeric features)
```

The quartile boundaries are only 1–2 points apart, and the noise (residual SD ≈ 2.5) is
small relative to the signal. A linear decision boundary therefore separates the bands
almost perfectly. Tree ensembles spend their capacity approximating that plane in steps
and do slightly worse.

This is a finding worth reporting, not a failure: **the data is close to linear, and the
simplest model captures it best.**

---

## 9. Ablation — old dataset vs new dataset

The previous dataset (`student-performance-predictions.csv`) scored 0.27 with |r| < 0.05
for every feature. Each factor was changed separately:

| Setup | Rows | Features | CV accuracy |
|---|---|---|---|
| Old dataset | 960 | 7 | 0.27 |
| New dataset | 960 | 7 | 0.65 |
| New dataset | 6,607 | 7 | 0.64 |
| New dataset | 960 | 19 | 0.69 |
| New dataset | 6,607 | 19 | 0.75 |

Changing the dataset at fixed size added ~0.38. Adding rows added nothing. Adding
features added ~0.11.

**The accuracy came from the data being informative, not from the data being larger.**

---

## 10. Limitations

1. The dataset is not Kenyan and not CBC-specific. It is a proxy for learner telemetry.
2. Bands are cohort-relative quartiles, not official KICD descriptors. "Below
   expectation" means below this group.
3. The score range is narrow (55–101), so band boundaries are 1–2 points apart.
4. Band counts are uneven (2,131 / 1,468 / 1,383 / 1,625) due to tied scores.
5. The dataset appears synthetic; relationships are plausible but not empirically Kenyan.
6. A production system should retrain on app telemetry labelled with teacher-assigned
   CBC bands.

---

## 11. Reproduce

```bash
python predictor/train_model.py      # train, CV, holdout, write bundle + metrics.json
python predictor/test_inference.py   # three sample learners
python predictor/evaluate.py         # dataset stats, correlations, CV, importances
```
