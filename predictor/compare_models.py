"""
Reproduce the model comparison quoted in ``REPORT.md`` and the regression
baselines documented in ``REGRESSION.md``.

Every model uses the exact same cleaned data, band definition and
preprocessing (``build_preprocessor`` imported from ``train_model``), so any
difference in the scores comes from the classifier alone.

Protocol
--------
* Stratified 5-fold cross-validation on all 6,607 rows (accuracy + macro F1),
  keeping the individual fold scores so the spread can be shown.
* One stratified 80/20 holdout, with a confusion matrix in band order.
* A plain least-squares fit on ``Exam_Score`` so the linear equation in
  ``REGRESSION.md`` (intercept 42.0, R2 0.57) is reproducible.

The logistic and linear baselines are discussed in ``REGRESSION.md``; the tree
models are discussed in ``REPORT.md``.

Output: ``predictor/model_comparison.json``

Run:  python predictor/compare_models.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from train_model import (
    BAND_LABELS,
    EXPECTED_COLUMNS,
    NUMERICAL_FEATURES,
    RANDOM_STATE,
    TARGET_COLUMN,
    assign_bands,
    build_preprocessor,
    clean_data,
    load_data,
)

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = SCRIPT_DIR / "model_comparison.json"


def build_models() -> dict[str, object]:
    """The four classifiers, all with the same preprocessing in front."""
    return {
        "Logistic Regression": LogisticRegression(max_iter=2000),
        "XGBoost": XGBClassifier(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            random_state=RANDOM_STATE,
            eval_metric="mlogloss",
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
    }


def main() -> None:
    df = load_data()
    df, _ = clean_data(df)
    df, cut_points = assign_bands(df)

    X = df[EXPECTED_COLUMNS]
    y = df["CBC_Band"]
    # XGBoost needs integer-encoded labels. This is the same encoder class
    # train_model.py stores in the artifact.
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    print(f"Rows: {len(df)}")
    print(f"Bands: {y.value_counts().sort_index().to_dict()}")
    print(f"Cut points: {cut_points}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scoring = {"accuracy": "accuracy", "f1_macro": "f1_macro"}

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, stratify=y_encoded, random_state=RANDOM_STATE
    )

    results: dict[str, dict] = {}

    print("\n" + "=" * 74)
    print(f"{'Model':<22}{'CV acc':>9}{'  +/-':>7}{'CV F1':>9}{'Holdout':>9}{'Time':>8}")
    print("=" * 74)

    for name, classifier in build_models().items():
        pipeline = Pipeline(
            [("preprocessor", build_preprocessor()), ("classifier", classifier)]
        )

        started = time.perf_counter()
        scores = cross_validate(
            pipeline, X, y_encoded, cv=cv, scoring=scoring, n_jobs=1
        )
        cv_seconds = time.perf_counter() - started

        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

        # Confusion matrix in difficulty order (BE, AE, ME, EE).
        # Labels and predictions are integer-encoded, so reorder the axes.
        raw_matrix = confusion_matrix(
            y_test, predictions, labels=range(len(encoder.classes_))
        )
        order = [list(encoder.classes_).index(band) for band in BAND_LABELS]
        ordered_matrix = raw_matrix[np.ix_(order, order)]

        results[name] = {
            "cv_accuracy_mean": round(float(scores["test_accuracy"].mean()), 4),
            "cv_accuracy_std": round(float(scores["test_accuracy"].std()), 4),
            "cv_accuracy_folds": [
                round(float(value), 4) for value in scores["test_accuracy"]
            ],
            "cv_f1_macro_mean": round(float(scores["test_f1_macro"].mean()), 4),
            "cv_f1_macro_std": round(float(scores["test_f1_macro"].std()), 4),
            "cv_f1_macro_folds": [
                round(float(value), 4) for value in scores["test_f1_macro"]
            ],
            "holdout_accuracy": round(float(accuracy_score(y_test, predictions)), 4),
            "holdout_f1_macro": round(float(f1_score(y_test, predictions, average="macro")), 4),
            "holdout_confusion_matrix": ordered_matrix.tolist(),
            "confusion_matrix_labels": BAND_LABELS,
            "cv_seconds": round(cv_seconds, 1),
        }

        row = results[name]
        print(
            f"{name:<22}{row['cv_accuracy_mean']:>9.3f}"
            f"{row['cv_accuracy_std']:>7.3f}{row['cv_f1_macro_mean']:>9.3f}"
            f"{row['holdout_accuracy']:>9.3f}{row['cv_seconds']:>7.1f}s"
        )
        folds = ", ".join(f"{value:.3f}" for value in row["cv_accuracy_folds"])
        print(f"{'  fold accuracies':<22}{folds}")

    print("=" * 74)

    # --- The linear fit quoted as evidence in the report -----------------
    # Predicts Exam_Score itself, not the band. It is not a classifier and
    # is not in the table above; it only shows how linear the data is.
    linear = {}
    for label, features in [
        ("three_features", ["Hours_Studied", "Attendance", "Previous_Scores"]),
        ("six_features", NUMERICAL_FEATURES),
    ]:
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("regressor", LinearRegression()),
            ]
        ).fit(df[features], df[TARGET_COLUMN])

        regressor = model[-1]
        linear[label] = {
            "features": features,
            "intercept": round(float(regressor.intercept_), 3),
            "coefficients": {
                feature: round(float(coefficient), 3)
                for feature, coefficient in zip(features, regressor.coef_)
            },
            "r2": round(float(model.score(df[features], df[TARGET_COLUMN])), 3),
        }

    print("\nLinear fit on Exam_Score (evidence only, not a classifier):")
    for label, fit in linear.items():
        print(
            f"  {label}: intercept {fit['intercept']}, "
            f"coefficients {fit['coefficients']}, R2 {fit['r2']}"
        )

    payload = {
        "random_state": RANDOM_STATE,
        "rows": int(len(df)),
        "features": len(EXPECTED_COLUMNS),
        "cut_points": [round(float(p), 3) for p in cut_points],
        "band_counts": {
            band: int(count) for band, count in y.value_counts().sort_index().items()
        },
        "cv": "stratified 5-fold on all rows",
        "holdout": "stratified 80/20",
        "models": results,
        "linear_score_fit": linear,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
