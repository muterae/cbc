# Presentation Notes — The Predictor

Simple explanations, the numbers to quote, and why XGBoost.

---

## 0. The 30-second version

> We built a model that reads a learner's study habits — attendance, study hours,
> previous scores — and places them in one of four CBC bands: Below, Approaching,
> Meeting, Exceeding. On 6,607 learners it gets about 75% of bands right, against
> 25% for random guessing. We compared three tree models and XGBoost was the most
> accurate.

---

## 1. What the model does

| Item | Value |
|---|---|
| Dataset | Student Performance Factors (Kaggle) |
| Rows | 6,607 learners |
| Features | 19 (attendance, hours studied, parental involvement, ...) |
| Target | `Exam_Score`, 55–101 |
| Output | One of four bands |
| Bands | quartiles: ≤65, 66–67, 68–69, ≥70 |

The model does **not** know about Grade 2 or any subject. It scores general
competency. The subject content is chosen later by the RAG layer.

---

## 2. The three models, explained simply

### Decision Tree — the flowchart

A tree asks yes/no questions until it reaches an answer.

```
Attendance > 90?  ── yes ──>  Study hours > 4?  ── yes ──> "Exceeding"
       │                              └── no ──> "Meeting"
       └── no ──> "Below"
```

It is easy to read, but a single tree memorises the training data, including the
noise. Change a few rows and the tree can change shape completely.

**On our data: 0.596.** The weakest model, and that is expected — one tree is unstable.

### Random Forest — the class vote

Build many trees, each on a random sample of rows and features, then let them vote.

One tree can be wrong; 200 trees rarely agree on the same wrong answer. Averaging
cancels individual mistakes.

**On our data: 0.703.** Better than one tree, still below XGBoost.

### XGBoost — the team that fixes mistakes

XGBoost also builds many trees, but not independently. It builds them **one at a time**,
and each new tree is trained on the errors the team is still making.

1. Make a first simple guess.
2. Look at where the guess is wrong.
3. Build a small tree that fixes those cases.
4. Add it to the team, but only a fraction of it (the learning rate).
5. Repeat 120 times.

That is what "boosting" means: many weak learners, each correcting the last one's
mistakes. The trees are kept small (depth 5) and each one contributes only a little
(learning rate 0.08), so the model improves gradually instead of memorising.

**On our data: 0.747.** The most accurate of the three.

---

## 3. How we score it

Accuracy alone hides where the model fails. We use a confusion matrix, then F1.

### 3.1 Confusion matrix — the full picture

Rows are the **truth**, columns are the **prediction**. The diagonal is correct; every
other cell is a specific mistake. This is XGBoost on the 1,322 held-out learners:

| Truth ↓ / Predicted → | Below | Approaching | Meeting | Exceeding | Total |
|---|---:|---:|---:|---:|---:|
| **Below** | **381** | 41 | 4 | 0 | 426 |
| **Approaching** | 57 | **176** | 58 | 3 | 294 |
| **Meeting** | 0 | 78 | **152** | 47 | 277 |
| **Exceeding** | 5 | 4 | 44 | **272** | 325 |

Two things to point out:

1. **The diagonal is strong at the ends.** 381 of 426 Below learners correct, 272 of
   325 Exceeding learners correct.
2. **The middle is where it breaks.** 58 Approaching learners were called Meeting, and
   78 Meeting learners were called Approaching. That single pair is 136 of the 341
   mistakes — 40% of all errors.

Accuracy is the diagonal divided by everything:

```
981 correct / 1,322 learners = 0.742
```

### 3.2 Precision and recall — two kinds of mistake

Take the Approaching column and row.

- **Precision** = when the model said Approaching, how often was it right?

  ```
  176 / (41 + 176 + 78 + 4) = 176 / 299 = 0.59
  ```

  The bottom of that fraction is the whole Approaching *column*: everyone the model
  named Approaching, right or wrong.

- **Recall** = of the learners who really are Approaching, how many did it find?

  ```
  176 / 294 = 0.60
  ```

  The bottom is the whole Approaching *row*: everyone who truly is Approaching.

In words: **precision is trust in the model's answer; recall is how much of the truth it
catches.** A model can be good at one and bad at the other — for example, it could catch
every Approaching learner by also labelling half the class Approaching (high recall, low
precision).

### 3.3 F1 — one number per band

F1 combines the two, using the harmonic mean:

```
F1 = 2 × (precision × recall) / (precision + recall)
```

For Approaching: `2 × (0.59 × 0.60) / (0.59 + 0.60) = 0.59`.

The harmonic mean is deliberately harsh: it stays low if **either** precision or recall
is low. A model with precision 1.00 and recall 0.20 gets F1 0.33, not 0.60. That is what
we want — a model that misses 80% of a band should not be flattered.

All four bands:

| Band | Precision | Recall | F1 | Learners |
|---|---:|---:|---:|---:|
| Below | 0.86 | 0.89 | 0.88 | 426 |
| Approaching | 0.59 | 0.60 | 0.59 | 294 |
| Meeting | 0.59 | 0.55 | 0.57 | 277 |
| Exceeding | 0.84 | 0.84 | 0.84 | 325 |

### 3.4 Macro F1 — the fair average

"Macro" means: compute F1 for each band, then take the **plain average**, so every band
counts the same.

```
macro F1 = (0.88 + 0.59 + 0.57 + 0.84) / 4 = 0.72
```

Why not just use accuracy? The bands are uneven (426 / 294 / 277 / 325 in the holdout).
Accuracy counts every learner equally, so the largest band dominates and a weak middle
band can hide. Macro F1 counts every **band** equally, which is why it exposes the 0.59
and 0.57.

That is the honest comparison: accuracy 0.742 looks fine; macro F1 0.720 shows where the
model is actually weak.

---

## 4. Validation — why the score can be trusted

### 4.1 One split is not enough

If we tested on a single 20% slice, the score could be lucky: that slice might contain
easy learners. We want two guarantees:

1. every learner is tested exactly once;
2. the score is not the product of one lucky slice, so we also report how much it moves.

### 4.2 Stratified 5-fold cross-validation, with 20 learners

Imagine 20 learners, five per band. Number them Below 1–5, Approaching 1–5, and so on.

Split them into five rounds. Each round holds out **one learner per band** (4 learners)
and trains on the other 16:

| Round | Held out (tested) | Used to train |
|---|---|---|
| 1 | Below 1, Approaching 1, Meeting 1, Exceeding 1 | the other 16 |
| 2 | Below 2, Approaching 2, Meeting 2, Exceeding 2 | the other 16 |
| 3 | Below 3, Approaching 3, Meeting 3, Exceeding 3 | the other 16 |
| 4 | Below 4, Approaching 4, Meeting 4, Exceeding 4 | the other 16 |
| 5 | Below 5, Approaching 5, Meeting 5, Exceeding 5 | the other 16 |

After five rounds, every learner has been tested exactly once, and nobody was ever
tested on data they were trained on. Score each round, then average the five scores.

**Why "stratified"?** Each round keeps the same band mix — one of each. Without it, a
round might get three Exceeding learners and one Below learner, and its score would jump
around for reasons that have nothing to do with the model.

**Why five?** Each round trains on 80% and tests on 20%. More folds means more training
time for little gain; fewer folds means noisier scores.

### 4.3 The real run — five actual scores

On the full dataset, each round tests about 1,321 learners and trains on about 5,286.
These are the real XGBoost fold accuracies:

| Fold | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| Accuracy | 0.741 | 0.729 | 0.761 | 0.768 | 0.734 |

```
mean = (0.741 + 0.729 + 0.761 + 0.768 + 0.734) / 5 = 0.747
```

The five scores stay inside a four-point range (0.729 to 0.768), so 0.747 is stable, not
a lucky split. The ±0.015 in the results table is the standard deviation of these five
numbers.

### 4.4 The holdout — one fixed 20%

Before any cross-validation, the data was split once: 5,285 learners for training, 1,322
for testing. The model is fitted on the 5,285 and scored once on the 1,322, giving
**0.742**. That is the run behind the confusion matrix in §3.1.

This is **not** the same 20% as a CV fold:

| | Holdout | CV fold |
|---|---|---|
| Type | one fixed split | five rotating splits |
| Tested | the same 1,322 every time | about 1,321 different learners each round |
| Trained on | the other 5,285 | the other ~5,286, refitted each round |
| Purpose | score the final model once | estimate the average and the spread |

> We do not score the 5,285 training rows and call that performance. The model has
> already seen those answers, so the number would be inflated. That is why the only
> reported score is on learners the final model never trained on.

One honesty note: the CV in §4.3 runs over all 6,607 learners, so the holdout learners do
appear in the CV folds. They never appear in the finally fitted model, which is what
makes 0.742 an honest score for it.

### 4.5 Why there is no leakage

The scaler and imputer sit **inside** the pipeline, so they are refitted on each training
fold and never see the test fold. Fitting them once on all the data would leak information
and inflate every score.

---

## 5. Results

Same cleaning, same folds, same holdout for every model.
Produced by `python predictor/compare_models.py`.

| Model | CV accuracy | Macro F1 | Holdout accuracy | Time |
|---|---:|---:|---:|---:|
| **XGBoost** | **0.747 ± 0.015** | **0.726** | **0.742** | 5.8 s |
| Random Forest | 0.703 ± 0.015 | 0.664 | 0.708 | 5.5 s |
| Decision Tree | 0.596 ± 0.011 | 0.572 | 0.589 | 0.9 s |
| Random guessing | 0.250 | — | — | — |

XGBoost per band on the holdout:

| Band | F1 |
|---|---:|
| Below Expectation | 0.88 |
| Approaching Expectation | 0.59 |
| Meeting Expectation | 0.57 |
| Exceeding Expectation | 0.84 |

The outer bands are learned well. The two middle bands are confused because their
boundaries are only one or two score points apart.

---

## 6. Why XGBoost?

1. **It is the most accurate of the three.** 0.747 against 0.703 for the forest and
   0.596 for a single tree. The gap is about four points, well above the fold-to-fold
   spread of ±0.015, so it is not luck.
2. **Each tree fixes the previous one's mistakes.** A random forest averages trees
   that were built independently, so a systematic error survives the vote. Boosting
   targets the errors directly.
3. **It is deliberately kept simple.** Shallow trees (depth 5) and a small learning
   rate (0.08) stop it from memorising. The gap between CV (0.747) and holdout (0.742)
   is tiny, which is the evidence that it is not overfitting.
4. **It handles mixed data.** Numbers and categories together, with some missing
   values (235 cells), without needing hand-built rules.
5. **It is the standard tool.** XGBoost is the default strong baseline in industry
   and in competitions, so the choice is easy to defend and easy to replace.

**Where it is weak, and you should say so:** the two middle bands score only 0.59 and
0.57. Those learners sit one or two marks apart, so the features we have cannot tell
them apart reliably. Better features — not a fancier model — are the fix.

---

## 7. Questions you will probably get

| Question | Short answer |
|---|---|
| What is a confusion matrix? | A table of true vs predicted; the diagonal is correct predictions |
| What is macro F1, and why not accuracy? | The average F1 across the four bands, so each band counts equally; accuracy would favour the biggest band |
| Why quartiles and not 40/60/80? | Scores are concentrated (55–101); fixed cut-offs would leave classes empty |
| Why cross-validation? | One split can be lucky; five folds give a mean and a spread |
| Why are AE and ME confused? | Their boundaries are 1–2 score points apart |
| Is 0.747 good? | Yes: 0.25 is random, and the outer bands reach 0.88 |
| Why is the tree worst? | One tree memorises noise; forests and boosting average that away |
| Why 200 trees in the forest but 120 in XGBoost? | A forest needs many independent votes; boosting needs fewer because each tree improves the last |
| Is it overfitting? | No: depth 5, learning rate 0.08, and CV 0.747 vs holdout 0.742 |
| Why not a bigger model? | More capacity would memorise noise; the middle bands need better features, not more trees |
| Is the data Kenyan or CBC? | No — it is a proxy. We retrain on app telemetry later |
| What was the old result? | 0.27, because the old dataset had no signal. The fix was the dataset, not more rows |
| What is data leakage? | Fitting the scaler on test data. We keep preprocessing inside the pipeline |

The ablation is a good slide: changing the dataset at the same size added ~0.38;
adding rows added nothing.

---

## 8. Numbers to memorise

- 6,607 learners, 19 features, 4 bands
- 0.747 XGBoost, 0.703 Forest, 0.596 Tree
- 0.742 — XGBoost on the holdout
- 0.726 — macro F1 (0.88 / 0.59 / 0.57 / 0.84 per band)
- 0.25 random
- Folds: 0.741, 0.729, 0.761, 0.768, 0.734
- cut points 65 / 67 / 69
- depth 5, learning rate 0.08, 120 trees

---

## 9. RAG progress, one line

The curriculum layer is being rebuilt: the Grade 3 Mathematics guide is extracted,
its 257 pages mapped into 3 terms and 14 sub-strands, and split into 149
lesson-level chunks ready for embedding. Grade 2 is dropped because the only Grade 2
document is a scan with no text layer.
