import json

import pytest
from fastapi.testclient import TestClient

import routers.quiz as quiz_router
from main import app
from retriever import RetrievedLesson
from services import generative_ai
from services.band_playbook import Band, get_playbook
from services.fallback_quiz import build_fallback_quiz
from services.profile_store import InMemoryProfileStore, get_profile_store

client = TestClient(app)


@pytest.fixture
def profile_store():
    store = InMemoryProfileStore(seed=False)
    app.dependency_overrides[get_profile_store] = lambda: store
    yield store
    app.dependency_overrides.pop(get_profile_store, None)


def payload_for(band: str) -> dict:
    playbook = get_playbook(band)
    return {
        "questions": [
            {
                "question_text": item.question_text,
                "options": item.options,
                "correct_answer": item.correct_answer,
                "hint": item.hint,
                "pedagogical_objective": item.pedagogical_objective,
            }
            for item in build_fallback_quiz(playbook)
        ],
        "teacher_insight_summary": "Learner is practising addition.",
    }


def test_adaptive_quiz_success(monkeypatch):
    monkeypatch.setattr(
        quiz_router,
        "retrieve_lessons",
        lambda *args, **kwargs: [RetrievedLesson("chunk-1", "Addition lesson.")],
    )
    monkeypatch.setattr(
        generative_ai,
        "_call_groq",
        lambda messages: json.dumps(payload_for("AE")),
    )

    response = client.post(
        "/api/v1/adaptive-quiz",
        json={
            "student_id": "std_001",
            "strand": "Addition",
            "session_type": "practice",
            "competency_band": "AE",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strand"] == "Numbers - Addition"
    assert body["competency_band"] == "Approaching Expectation"
    assert len(body["questions"]) == 5
    assert body["questions"][0]["options"][0].startswith("A) ")


def test_adaptive_quiz_uses_fallback(monkeypatch):
    monkeypatch.setattr(
        quiz_router,
        "retrieve_lessons",
        lambda *args, **kwargs: [RetrievedLesson("chunk-1", "Addition lesson.")],
    )

    def fail(messages):
        raise RuntimeError("Groq unavailable")

    monkeypatch.setattr(generative_ai, "_call_groq", fail)

    response = client.post(
        "/api/v1/adaptive-quiz",
        json={
            "student_id": "std_001",
            "strand": "Subtraction",
            "competency_band": "EE",
        },
    )

    assert response.status_code == 200
    assert len(response.json()["questions"]) == 6


def test_adaptive_quiz_rejects_unknown_band():
    response = client.post(
        "/api/v1/adaptive-quiz",
        json={
            "student_id": "std_001",
            "strand": "Addition",
            "competency_band": "Unknown",
        },
    )

    assert response.status_code == 400


def test_adaptive_quiz_rejects_unknown_strand():
    response = client.post(
        "/api/v1/adaptive-quiz",
        json={
            "student_id": "std_001",
            "strand": "Geography",
            "competency_band": "Meeting Expectation",
        },
    )

    assert response.status_code == 400


def test_adaptive_quiz_requires_student_id():
    response = client.post(
        "/api/v1/adaptive-quiz",
        json={"strand": "Addition"},
    )

    assert response.status_code == 422


def test_adaptive_quiz_uses_profile_band(profile_store, monkeypatch):
    profile_store.upsert("std_001", "Amina")
    profile_store.save_placement(
        "std_001",
        "intro-v1",
        9,
        12,
        {"BE": 3, "AE": 3, "ME": 2, "EE": 1},
        Band.ME,
    )
    monkeypatch.setattr(
        quiz_router,
        "retrieve_lessons",
        lambda *args, **kwargs: [RetrievedLesson("chunk-1", "Addition lesson.")],
    )
    monkeypatch.setattr(
        generative_ai,
        "_call_groq",
        lambda messages: json.dumps(payload_for("ME")),
    )

    response = client.post(
        "/api/v1/adaptive-quiz",
        json={"student_id": "std_001", "strand": "Addition"},
    )

    assert response.status_code == 200
    assert response.json()["competency_band"] == Band.ME.value


def test_adaptive_quiz_rejects_unknown_profile():
    response = client.post(
        "/api/v1/adaptive-quiz",
        json={"student_id": "std_missing", "strand": "Addition"},
    )

    assert response.status_code == 404


def test_adaptive_quiz_requires_completed_placement(profile_store):
    profile_store.upsert("std_001", "Amina")

    response = client.post(
        "/api/v1/adaptive-quiz",
        json={"student_id": "std_001", "strand": "Addition"},
    )

    assert response.status_code == 409
