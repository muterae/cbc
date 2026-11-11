from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import routers.profiles as profiles_router
from main import app
from services.band_playbook import Band
from services.intro_quiz import IntroQuiz, _fallback_band
from services.profile_store import InMemoryProfileStore, get_profile_store

client = TestClient(app)


def fallback_quiz() -> IntroQuiz:
    questions = []
    for band in Band:
        questions.extend(_fallback_band(band))
    questions = [
        question.model_copy(update={"question_number": number})
        for number, question in enumerate(questions, start=1)
    ]
    return IntroQuiz(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source="fallback",
        questions=questions,
    )


@pytest.fixture
def store():
    instance = InMemoryProfileStore(seed=False)
    app.dependency_overrides[get_profile_store] = lambda: instance
    yield instance
    app.dependency_overrides.pop(get_profile_store, None)


def create_profile() -> None:
    response = client.post(
        "/api/v1/profiles",
        json={
            "student_id": "std_001",
            "name": "Amina",
            "grade": "Grade 3",
            "class_name": "3A",
            "term": "Term 1",
        },
    )
    assert response.status_code == 200


def test_create_and_get_profile(store):
    create_profile()

    response = client.get("/api/v1/profiles/std_001")

    assert response.status_code == 200
    assert response.json()["name"] == "Amina"
    assert response.json()["placement_completed"] is False


def test_submit_placement(store, monkeypatch):
    create_profile()
    quiz = fallback_quiz()
    monkeypatch.setattr(profiles_router, "get_intro_quiz", lambda: quiz)

    response = client.post(
        "/api/v1/profiles/std_001/placement",
        json={
            "quiz_id": quiz.quiz_id,
            "answers": [
                {
                    "question_number": question.question_number,
                    "selected_option": question.correct_answer,
                }
                for question in quiz.questions
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["correct"] == 12
    assert body["result"]["band"] == Band.EE.value
    assert body["profile"]["placement_completed"] is True
    assert body["profile"]["band_status"] == "provisional"


def test_placement_is_idempotent(store, monkeypatch):
    create_profile()
    quiz = fallback_quiz()
    monkeypatch.setattr(profiles_router, "get_intro_quiz", lambda: quiz)
    payload = {
        "quiz_id": quiz.quiz_id,
        "answers": [
            {
                "question_number": question.question_number,
                "selected_option": question.correct_answer,
            }
            for question in quiz.questions
        ],
    }

    first = client.post("/api/v1/profiles/std_001/placement", json=payload)
    second = client.post("/api/v1/profiles/std_001/placement", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_placement_rejects_wrong_quiz_version(store, monkeypatch):
    create_profile()
    quiz = fallback_quiz()
    monkeypatch.setattr(profiles_router, "get_intro_quiz", lambda: quiz)

    response = client.post(
        "/api/v1/profiles/std_001/placement",
        json={"quiz_id": "intro-v2", "answers": []},
    )

    assert response.status_code == 409


def test_placement_requires_every_answer(store, monkeypatch):
    create_profile()
    quiz = fallback_quiz()
    monkeypatch.setattr(profiles_router, "get_intro_quiz", lambda: quiz)

    response = client.post(
        "/api/v1/profiles/std_001/placement",
        json={
            "quiz_id": quiz.quiz_id,
            "answers": [
                {
                    "question_number": quiz.questions[0].question_number,
                    "selected_option": quiz.questions[0].correct_answer,
                }
            ],
        },
    )

    assert response.status_code == 400


def test_placement_rejects_unknown_profile(monkeypatch):
    quiz = fallback_quiz()
    monkeypatch.setattr(profiles_router, "get_intro_quiz", lambda: quiz)

    response = client.post(
        "/api/v1/profiles/std_missing/placement",
        json={"quiz_id": quiz.quiz_id, "answers": []},
    )

    assert response.status_code == 404
