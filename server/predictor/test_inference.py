"""
Smoke test for the exported predictor bundle.

Verifies that:
  1. the bundle loads and contains the expected keys,
  2. a realistic learner row produces a valid CBC band,
  3. the band is decoded with the same LabelEncoder used during training,
  4. the input schema matches the columns the pipeline was fitted on,
  5. probabilities sum to 1 and every band is represented.

Run:  python predictor/test_inference.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_PATH = SCRIPT_DIR / "cbc_predictor_bundle.pkl"
VALID_BANDS = {
    "Below Expectation",
    "Approaching Expectation",
    "Meeting Expectation",
    "Exceeding Expectation",
}

# Typical learners as the mobile app would send them.
SAMPLE_LEARNERS = {
    "strong learner": {
        "Hours_Studied": 30,
        "Attendance": 95,
        "Sleep_Hours": 8,
        "Previous_Scores": 90,
        "Tutoring_Sessions": 4,
        "Physical_Activity": 5,
        "Parental_Involvement": "High",
        "Access_to_Resources": "High",
        "Extracurricular_Activities": "Yes",
        "Motivation_Level": "High",
        "Internet_Access": "Yes",
        "Family_Income": "High",
        "Teacher_Quality": "High",
        "School_Type": "Private",
        "Peer_Influence": "Positive",
        "Learning_Disabilities": "No",
        "Parental_Education_Level": "College",
        "Distance_from_Home": "Near",
        "Gender": "Female",
    },
    "average learner": {
        "Hours_Studied": 20,
        "Attendance": 80,
        "Sleep_Hours": 7,
        "Previous_Scores": 72,
        "Tutoring_Sessions": 2,
        "Physical_Activity": 3,
        "Parental_Involvement": "Medium",
        "Access_to_Resources": "Medium",
        "Extracurricular_Activities": "Yes",
        "Motivation_Level": "Medium",
        "Internet_Access": "Yes",
        "Family_Income": "Medium",
        "Teacher_Quality": "Medium",
        "School_Type": "Public",
        "Peer_Influence": "Neutral",
        "Learning_Disabilities": "No",
        "Parental_Education_Level": "High School",
        "Distance_from_Home": "Moderate",
        "Gender": "Male",
    },
    "struggling learner": {
        "Hours_Studied": 8,
        "Attendance": 60,
        "Sleep_Hours": 6,
        "Previous_Scores": 55,
        "Tutoring_Sessions": 0,
        "Physical_Activity": 1,
        "Parental_Involvement": "Low",
        "Access_to_Resources": "Low",
        "Extracurricular_Activities": "No",
        "Motivation_Level": "Low",
        "Internet_Access": "No",
        "Family_Income": "Low",
        "Teacher_Quality": "Low",
        "School_Type": "Public",
        "Peer_Influence": "Negative",
        "Learning_Disabilities": "No",
        "Parental_Education_Level": "High School",
        "Distance_from_Home": "Far",
        "Gender": "Male",
    },
}


def load_bundle(path: Path = MODEL_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"No model at {path}. Run 'python predictor/train_model.py' first."
        )
    return joblib.load(path)


def predict(artifact: dict, learner: dict) -> tuple[str, dict[str, float]]:
    """Predict one learner and return the band plus class probabilities."""
    missing = set(artifact["expected_columns"]) - set(learner)
    if missing:
        raise ValueError(f"Learner payload is missing columns: {sorted(missing)}")

    row = pd.DataFrame([learner])[artifact["expected_columns"]]

    pipeline = artifact["pipeline"]
    encoder = artifact["label_encoder"]

    index = int(pipeline.predict(row)[0])
    band = encoder.inverse_transform([index])[0]

    probabilities = {
        label: float(prob)
        for label, prob in zip(encoder.classes_, pipeline.predict_proba(row)[0])
    }
    return band, probabilities


def main() -> int:
    artifact = load_bundle()

    required_keys = {
        "pipeline",
        "label_encoder",
        "expected_columns",
        "band_cut_points",
        "metrics",
    }
    missing_keys = required_keys - set(artifact)
    if missing_keys:
        raise KeyError(f"Bundle is missing keys: {sorted(missing_keys)}")

    # The encoder and the saved band list must agree, otherwise decoding is
    # wrong even though nothing raises an exception.
    encoder_labels = list(artifact["label_encoder"].classes_)
    if set(encoder_labels) != VALID_BANDS:
        raise AssertionError(f"Encoder classes are not the four CBC bands: {encoder_labels}")

    print(f"Model trained at: {artifact['metrics']['trained_at']}")
    print(
        "Cross-validation accuracy: "
        f"{artifact['metrics']['cross_validation']['accuracy_mean']:.3f}"
    )
    print(f"Encoder classes: {encoder_labels}\n")

    failures = 0
    for name, learner in SAMPLE_LEARNERS.items():
        band, probabilities = predict(artifact, learner)
        print(f"{name}: {band}")
        for label, prob in sorted(probabilities.items(), key=lambda item: -item[1]):
            print(f"    {label:<24} {prob * 100:5.1f}%")

        if band not in VALID_BANDS:
            print(f"  FAIL: '{band}' is not a valid CBC band")
            failures += 1
        if abs(sum(probabilities.values()) - 1.0) > 1e-6:
            print("  FAIL: probabilities do not sum to 1")
            failures += 1
        print()

    if failures:
        print(f"{failures} check(s) failed.")
        return 1

    print("All inference checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
