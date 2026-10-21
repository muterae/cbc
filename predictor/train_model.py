"""
Train an XGBoost classifier that maps learner telemetry to a CBC competency band.

Dataset
-------
Kaggle "Student Performance Factors" (lainguyn123 / student-performance-factors):
6,607 learners, 19 features, target ``Exam_Score``. The columns match the app's
telemetry schema (hours studied, attendance, parental involvement, internet
access, tutoring, gender, ...) and carry real predictive signal.

Key design points
-----------------
1. The CSV is cached in ``predictor/data``; Kaggle is only contacted if it is
   missing, so training works offline and is reproducible.
2. Rows with a missing ``Exam_Score`` are dropped. They cannot be supervised.
3. ``Exam_Score`` is clipped to 0-100; the raw file contains one impossible 101.
4. Four bands are built from the 25/50/75th percentiles of ``Exam_Score`` and
   the cut points are stored in the artifact, so inference reproduces the exact
   same definition.
5. One ``LabelEncoder`` handles both encoding and decoding. Predictions can no
   longer be decoded with a mismatched hand-written dictionary.
6. Stratified 5-fold cross-validation is reported alongside the holdout score.

Run:  python predictor/train_model.py
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
DATA_PATH = DATA_DIR / "student-performance-factors.csv"
MODEL_PATH = SCRIPT_DIR / "cbc_predictor_bundle.pkl"
METRICS_PATH = SCRIPT_DIR / "metrics.json"

KAGGLE_SLUG = "lainguyn123/student-performance-factors"
RANDOM_STATE = 42

# Ordered from lowest to highest. Used only to label the quartile buckets.
BAND_LABELS = [
    "Below Expectation",
    "Approaching Expectation",
    "Meeting Expectation",
    "Exceeding Expectation",
]

# Features the mobile app can actually log or ask the learner/teacher for.
NUMERICAL_FEATURES = [
    "Hours_Studied",       # weekly practice time
    "Attendance",          # class attendance rate
    "Sleep_Hours",         # average nightly sleep
    "Previous_Scores",     # running average of past assessments
    "Tutoring_Sessions",   # extra support received
    "Physical_Activity",   # weekly activity level
]

CATEGORICAL_FEATURES = [
    "Parental_Involvement",
    "Access_to_Resources",
    "Extracurricular_Activities",
    "Motivation_Level",
    "Internet_Access",
    "Family_Income",
    "Teacher_Quality",
    "School_Type",
    "Peer_Influence",
    "Learning_Disabilities",
    "Parental_Education_Level",
    "Distance_from_Home",
    "Gender",
]

EXPECTED_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "Exam_Score"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read the cached CSV, downloading it from Kaggle only when absent."""
    if not path.exists():
        import kagglehub

        print(f"{path} not found, downloading {KAGGLE_SLUG} from Kaggle...")
        download_dir = Path(kagglehub.dataset_download(KAGGLE_SLUG))
        csv_files = sorted(download_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV found in Kaggle download at {download_dir}")

        # Cache a copy so later runs never need the network.
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(csv_files[0], path)
        print(f"Cached dataset at {path}")

    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")
    return df


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean the raw dataframe and return it with a log of what changed."""
    df = df.copy()
    log: dict[str, object] = {"rows_loaded": int(len(df))}

    # 1. A row without a target cannot be used for supervised learning.
    missing_target = df[TARGET_COLUMN].isna()
    log["rows_missing_target"] = int(missing_target.sum())
    df = df.loc[~missing_target].copy()

    # 2. Drop duplicate records.
    before = len(df)
    df = df.drop_duplicates().copy()
    log["duplicate_rows_removed"] = int(before - len(df))

    # 3. Exam scores above 100 are impossible (one row in this file).
    invalid_scores = int((df[TARGET_COLUMN] > 100).sum())
    df[TARGET_COLUMN] = df[TARGET_COLUMN].clip(lower=0, upper=100)
    log["exam_scores_clipped"] = invalid_scores

    # 4. Attendance cannot exceed 100% either.
    invalid_attendance = int((df["Attendance"] > 100).sum())
    df["Attendance"] = df["Attendance"].clip(lower=0, upper=100)
    log["attendance_values_clipped"] = invalid_attendance

    # 5. Standardise category spelling so one-hot columns stay stable.
    for column in CATEGORICAL_FEATURES:
        df[column] = df[column].str.strip().str.title()

    log["rows_after_cleaning"] = int(len(df))
    log["missing_feature_values"] = int(df[EXPECTED_COLUMNS].isna().sum().sum())
    log["missing_values_by_column"] = {
        column: int(count)
        for column, count in df[EXPECTED_COLUMNS].isna().sum().items()
        if count > 0
    }
    return df, log


# ---------------------------------------------------------------------------
# Target creation
# ---------------------------------------------------------------------------
def assign_bands(
    df: pd.DataFrame, cut_points: list[float] | None = None
) -> tuple[pd.DataFrame, list[float]]:
    """Turn ``Exam_Score`` into four quartile bands.

    The four CBC labels are kept because the downstream RAG layer expects them.
    Quartiles are used instead of fixed 40/60/80 cut-offs because the observed
    scores are concentrated in a narrow band; fixed cut-offs leave classes empty.
    """
    df = df.copy()

    if cut_points is None:
        quantiles = df[TARGET_COLUMN].quantile([0.25, 0.50, 0.75]).to_numpy()
        if len(np.unique(quantiles)) < 3:
            raise ValueError(
                "Exam_Score has too many tied values to build four quartile bands."
            )
        cut_points = [float(q) for q in quantiles]

    lower, middle_low, middle_high = cut_points
    bins = [-np.inf, lower, middle_low, middle_high, np.inf]

    df["CBC_Band"] = pd.cut(df[TARGET_COLUMN], bins=bins, labels=BAND_LABELS)
    df = df.dropna(subset=["CBC_Band"]).copy()
    df["CBC_Band"] = df["CBC_Band"].astype(str)

    return df, [float(p) for p in cut_points]


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def build_pipeline() -> Pipeline:
    """Full preprocessing + classifier pipeline.

    All preprocessing lives inside the pipeline so cross-validation refits it on
    each fold. That is what prevents data leakage.
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    classifier = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        random_state=RANDOM_STATE,
        eval_metric="mlogloss",
    )

    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    df = load_data()
    df, cleaning_log = clean_data(df)
    df, cut_points = assign_bands(df)

    print("\nCleaning log:")
    for key, value in cleaning_log.items():
        print(f"  {key}: {value}")

    print("\nBand distribution (quartiles of Exam_Score):")
    print(df["CBC_Band"].value_counts().sort_index())
    print(f"Cut points: {cut_points}")

    X = df[EXPECTED_COLUMNS]
    y = df["CBC_Band"]

    # One encoder is used for training and for decoding at inference time.
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    print(f"\nEncoder classes: {list(label_encoder.classes_)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y_encoded,
    )

    pipeline = build_pipeline()

    # ---- Cross-validation on the training split -------------------------
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_results = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring={"accuracy": "accuracy", "f1_macro": "f1_macro"},
        n_jobs=1,
    )
    cv_accuracy = cv_results["test_accuracy"]
    cv_f1 = cv_results["test_f1_macro"]
    print("\n5-fold cross-validation (training split)")
    print(f"  accuracy: {cv_accuracy.mean():.3f} +/- {cv_accuracy.std():.3f}")
    print(f"  macro F1: {cv_f1.mean():.3f} +/- {cv_f1.std():.3f}")

    # ---- Final fit and holdout evaluation -------------------------------
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    report = classification_report(
        y_test,
        y_pred,
        labels=range(len(label_encoder.classes_)),
        target_names=list(label_encoder.classes_),
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=range(len(label_encoder.classes_)))

    print("\nHoldout classification report:")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=range(len(label_encoder.classes_)),
            target_names=list(label_encoder.classes_),
            zero_division=0,
        )
    )
    print("Confusion matrix (rows = actual, columns = predicted):")
    print(cm)

    metrics = {
        "dataset": {
            "name": "Student Performance Factors (Kaggle: lainguyn123)",
            "rows_loaded": cleaning_log["rows_loaded"],
            "rows_used": int(len(df)),
            "features": EXPECTED_COLUMNS,
            "target": "CBC_Band (quartiles of Exam_Score)",
            "band_cut_points": cut_points,
            "band_counts": df["CBC_Band"].value_counts().sort_index().to_dict(),
        },
        "cleaning": cleaning_log,
        "cross_validation": {
            "folds": 5,
            "accuracy_mean": float(cv_accuracy.mean()),
            "accuracy_std": float(cv_accuracy.std()),
            "f1_macro_mean": float(cv_f1.mean()),
            "f1_macro_std": float(cv_f1.std()),
        },
        "holdout": {
            "accuracy": float(report["accuracy"]),
            "macro_f1": float(report["macro avg"]["f1-score"]),
            "weighted_f1": float(report["weighted avg"]["f1-score"]),
            "per_class": {
                label: {
                    "precision": float(report[label]["precision"]),
                    "recall": float(report[label]["recall"]),
                    "f1": float(report[label]["f1-score"]),
                    "support": int(report[label]["support"]),
                }
                for label in label_encoder.classes_
            },
            "confusion_matrix": cm.tolist(),
            "class_labels": list(label_encoder.classes_),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "versions": {
            "python": ".".join(map(str, sys.version_info[:3])),
            "scikit-learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }

    # ---- Persist -------------------------------------------------------
    artifact = {
        "pipeline": pipeline,
        "label_encoder": label_encoder,
        "expected_columns": EXPECTED_COLUMNS,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "band_labels": BAND_LABELS,
        "band_cut_points": cut_points,
        "metrics": metrics,
    }
    joblib.dump(artifact, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"\nSaved model bundle to {MODEL_PATH}")
    print(f"Saved metrics report to {METRICS_PATH}")
    print("Decode predictions with: artifact['label_encoder'].inverse_transform([idx])[0]")


if __name__ == "__main__":
    main()
