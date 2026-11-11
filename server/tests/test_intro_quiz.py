from datetime import datetime, timezone

from fastapi.testclient import TestClient

import routers.intro_quiz as intro_router
from main import app
from services.band_playbook import Band
from services.intro_quiz import (
    IntroQuiz,
    _fallback_band,
    clear_intro_quiz_cache,
    get_intro_quiz,
    save_snapshot,
    to_response,
    validate_intro_quiz,
)
from services import intro_quiz

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


def test_fallback_quiz_is_structurally_valid():
    quiz = fallback_quiz()

    assert len(quiz.questions) == 12
    assert validate_intro_quiz(quiz) == []
    assert {band.name for band in Band} == {question.band.name for question in quiz.questions}


def test_public_response_hides_answers_and_hints():
    response = to_response(fallback_quiz())
    payload = response.model_dump()

    assert len(payload["questions"]) == 12
    assert "correct_answer" not in payload["questions"][0]
    assert "hint" not in payload["questions"][0]
    assert payload["questions"][0]["band"] == "Below Expectation"


def test_intro_quiz_endpoint_returns_cached_quiz(monkeypatch):
    quiz = fallback_quiz()
    monkeypatch.setattr(intro_router, "get_intro_quiz", lambda: quiz)

    first = client.get("/api/v1/intro-quiz")
    second = client.get("/api/v1/intro-quiz")

    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.json()["quiz_id"] == "intro-v1"
    assert len(first.json()["questions"]) == 12


def test_get_intro_quiz_caches_result(monkeypatch):
    quiz = fallback_quiz()
    clear_intro_quiz_cache()
    monkeypatch.setattr(intro_quiz, "_load_snapshot", lambda: quiz)

    first = get_intro_quiz()
    second = get_intro_quiz()

    assert first is second
    clear_intro_quiz_cache()


def test_committed_snapshot_is_valid():
    loaded = intro_quiz._load_snapshot()

    assert loaded is not None
    assert loaded.quiz_id == "intro-v1"
    assert len(loaded.questions) == 12
    assert validate_intro_quiz(loaded) == []


def test_snapshot_round_trip(tmp_path, monkeypatch):
    path = tmp_path / "intro_quiz.json"
    monkeypatch.setattr(intro_quiz, "SNAPSHOT_PATH", path)
    quiz = fallback_quiz()

    save_snapshot(quiz)
    loaded = intro_quiz._load_snapshot()

    assert loaded is not None
    assert loaded.quiz_id == quiz.quiz_id
    assert len(loaded.questions) == 12
