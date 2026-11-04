"""
Print the statistics needed for the Deliverable 2 notebook.

Reports:
  * dataset shape, missing values and band distribution,
  * correlation of each numeric feature with FinalGrade,
  * stratified 5-fold cross-validation on the full cleaned dataset,
  * the most important features according to the saved XGBoost model.

Run:  python predictor/evaluate.py
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate

from train_model import (
    EXPECTED_COLUMNS,
    METRICS_PATH,
    MODEL_PATH,
    NUMERICAL_FEATURES,
    RANDOM_STATE,
    TARGET_COLUMN,
    assign_bands,
    clean_data,
    load_data,
)


def main() -> None:
    artifact = joblib.load(MODEL_PATH)
    df = load_data()
    df, cleaning_log = clean_data(df)
    df, cut_points = assign_bands(df, artifact["band_cut_points"])

    print("\n=== Dataset ===")
    print(f"Rows used for modelling : {len(df)}")
    print(f"Features                : {len(EXPECTED_COLUMNS)}")
    print(f"Missing feature values    : {cleaning_log['missing_feature_values']}")
    print("\nBand distribution:")
    print(df["CBC_Band"].value_counts().sort_index())

    print("\n=== Correlation with Exam_Score ===")
    correlations = (
        df[NUMERICAL_FEATURES + [TARGET_COLUMN]]
        .corr(numeric_only=True)[TARGET_COLUMN]
        .drop(TARGET_COLUMN)
        .sort_values(ascending=False)
    )
    for feature, value in correlations.items():
        print(f"  {feature:<24} {value:+.3f}")

    print("\n=== 5-fold cross-validation (full dataset) ===")
    X = df[EXPECTED_COLUMNS]
    # The saved pipeline expects the encoded integer target, not the band text.
    y = artifact["label_encoder"].transform(df["CBC_Band"])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results = cross_validate(
        artifact["pipeline"],
        X,
        y,
        cv=cv,
        scoring={"accuracy": "accuracy", "f1_macro": "f1_macro"},
        n_jobs=1,
    )
    for metric in ("accuracy", "f1_macro"):
        scores = results[f"test_{metric}"]
        print(f"  {metric:<10} {scores.mean():.3f} +/- {scores.std():.3f}")

    print("\n=== Feature importance (saved XGBoost model) ===")
    preprocessor = artifact["pipeline"].named_steps["preprocessor"]
    classifier = artifact["pipeline"].named_steps["classifier"]
    names = preprocessor.get_feature_names_out()
    importances = pd.Series(classifier.feature_importances_, index=names)
    for name, value in importances.sort_values(ascending=False).head(10).items():
        print(f"  {name:<32} {value:.3f}")

    if METRICS_PATH.exists():
        print(f"\nTraining metrics snapshot: {METRICS_PATH}")


if __name__ == "__main__":
    main()
