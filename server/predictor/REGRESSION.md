# Regression Baselines — Linear and Logistic

A separate record of the two regression models tested against the tree models.

This study is **not part of the deployed model**. The predictor of record is XGBoost,
documented in [REPORT.md](REPORT.md). Nothing here is hidden or discarded: the code that
produces these numbers is `compare_models.py`, and the raw output is in
`model_comparison.json`. It lives in its own file because the deployed architecture does
not depend on it yet.

---

## 1. Two models, two different jobs

The names are similar and that causes most of the confusion. They answer different
questions.

| | Linear regression | Logistic regression |
|---|---|---|
| Question | **How much?** | **Which group?** |
| Output | any number, e.g. 63.2 | probability 0–1, then a class |
| Example | "this learner will score 63" | "72% chance of Meeting" |
| Shape | straight line | straight line bent into an S |
| Fitted by | least squares, one formula | maximum likelihood, iterative |
| Used here for | evidence about the data | a classifier (0.950) |

### 1.1 Linear regression

It finds the straight line that makes the total squared error smallest:

```
score = b0 + b1 × hours + b2 × attendance + b3 × previous_scores
```

"Least squares" means: try different weights, and keep the ones where the vertical
distance between each learner and the line is smallest overall. There is a closed-form
solution, so it is computed in one step.

### 1.2 Logistic regression

It starts with the same weighted sum, then turns it into a probability:

```
z = w0 + w1 × x1 + ... + wn × xn
p = 1 / (1 + e^(-z))
```

A large `z` gives a probability near 1; a very negative `z` gives one near 0. For four
bands, the model produces four scores and normalises them (softmax), then returns the
band with the highest probability.

There is no one-step formula for the weights. They are found by repeatedly adjusting
them to reduce the log-loss — an iterative process, which is why `max_iter=2000` is set
in the script.

---

## 2. How they were evaluated

The protocol is identical to the tree comparison in [REPORT.md §8](REPORT.md#8-model-comparison):

1. Same cleaned data: 6,607 learners, 19 features.
2. Same bands: quartiles of `Exam_Score`, cut points 65 / 67 / 69.
3. Same preprocessing: median imputation and scaling for numeric features, most-frequent
   imputation and one-hot encoding for categorical features, all inside the pipeline.
4. Same folds: stratified 5-fold cross-validation on all rows.
5. Same holdout: one stratified 80/20 split.

Only the classifier changes, so any difference in score comes from the model.

**Configuration:** `LogisticRegression(max_iter=2000)`, multinomial loss, no class
weights; the CV folds and holdout use seed 42.

---

## 3. Logistic regression results

| Metric | Value |
|---|---|
| CV accuracy | **0.950 ± 0.006** |
| CV macro F1 | **0.947 ± 0.006** |
| Holdout accuracy | **0.945** |
| Holdout macro F1 | 0.941 |
| CV time | 1.8 s |
| Random baseline (4 classes) | 0.250 |

For comparison, the tree models score 0.747 (XGBoost), 0.703 (Random Forest) and 0.596
(Decision Tree). The linear classifier is far ahead on this dataset.

The model produces a weight set for each band. Those coefficients are not listed here
because the one-hot encoding expands the 19 features into 40 columns, so the table would
be mostly dummy-variable weights. They can be read from a fitted pipeline
if needed.

---

## 4. Linear regression on the score

This is **not** a classifier. It predicts `Exam_Score` itself, and it is included because
it explains *why* the linear classifier does so well.

### 4.1 Equation (three strongest features)

```
Exam_Score ≈ 42.002 + 0.290 × Hours_Studied + 0.198 × Attendance + 0.048 × Previous_Scores
```

| Term | Meaning |
|---|---|
| 42.002 | intercept — the prediction at zero on all three features (extrapolation; no learner in the data is there) |
| 0.290 | one more study hour per week → about +0.29 marks |
| 0.198 | one more attendance point → about +0.20 marks |
| 0.048 | one more previous-score point → about +0.05 marks |

### 4.2 Fit quality

| Features | R² |
|---|---:|
| Hours, Attendance, Previous Scores | 0.572 |
| All six numeric features | 0.598 |

R² measures how much of the variation in scores the line explains:

- R² = 0 → no better than always guessing the average score.
- R² = 1 → a perfect line.
- 0.57 → the line removes 57% of the error; 43% is left to factors not in the data.

In raw terms: scores vary with a standard deviation of about 3.8 points, and the line
leaves a residual standard deviation of about 2.5 points.

### 4.3 Caveat

This R² is fitted on **all** rows, with no train/test split, so it is an in-sample,
slightly optimistic figure. The 0.950 above is cross-validated and is the number to
quote for the classifier. The two are not comparable: one measures how well a number is
predicted, the other how often a band is correct.

---

## 5. Findings

1. **The target is close to linear.** Study hours, attendance and previous scores explain
   just over half of the variation in scores, with a simple straight line.
2. **A straight boundary separates the bands well.** The quartile boundaries sit one or
   two marks apart. If the score is a near-linear function of the features, thresholds on
   that score are near-linear boundaries, and logistic regression finds them almost
   perfectly.
3. **Tree models spend effort approximating a plane.** XGBoost builds a staircase of
   small boxes to represent a surface that is almost flat. It gets close (0.747) but not
   as close as the model whose shape already matches the data.
4. **This is a property of the dataset, not a permanent verdict.** The dataset is a
   smooth proxy. Real learner telemetry is likely to contain interactions (attendance ×
   study time), outliers and missing values, where boosted trees usually overtake a
   linear model.

---

## 6. Why XGBoost is still the model of record

- It is the assigned base model for this deliverable (`XGBoost_Base.ipynb`); the
  regression study is a baseline, not the architecture.
- It is expected to generalise better to real app telemetry, where relationships are
  unlikely to stay linear.
- It captures feature interactions without hand-built terms, which the linear model
  cannot do.

Logistic regression remains the baseline that any future model must beat. If real
telemetry confirms the linear relationship, it is the natural candidate to deploy: it is
simpler, faster, smaller and more interpretable. That decision needs data from the app,
not from this proxy.

---

## 7. Limitations

1. The dataset is not Kenyan and not CBC-specific. It is a proxy.
2. The linear fit is in-sample (no held-out R² is reported).
3. R² describes score prediction, not band classification.
4. Correlation is not causation: attendance correlates with scores, but the model does
   not prove that raising attendance raises scores.
5. The bands are cohort-relative quartiles, not official KICD descriptors.

---

## 8. Reproduce

```bash
python predictor/compare_models.py
```

This writes `model_comparison.json`, which contains:

- `models` — CV accuracy, CV macro F1, holdout accuracy and time for all four models;
- `linear_score_fit` — intercept, coefficients and R² for the three-feature and
  six-feature least-squares fits.

The comparison table in [REPORT.md §8](REPORT.md#8-model-comparison) uses the three tree
models from the same run, so both documents are generated from one script.
