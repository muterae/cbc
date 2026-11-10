import json

import pytest

from retriever import RetrievedLesson
from services import generative_ai
from services.band_playbook import get_playbook
from services.curriculum import resolve_location
from services.fallback_quiz import build_fallback_quiz
from services.generative_ai import (
    QuizGenerationError,
    _parse_questions,
    build_messages,
    generate_quiz,
)
from services.quiz import AdaptiveQuizRequest


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
        "teacher_insight_summary": "Generated summary.",
    }


def request_for(band: str = "AE") -> AdaptiveQuizRequest:
    return AdaptiveQuizRequest(
        student_id="std_test_001",
        strand="Addition",
        competency_band=band,
    )


def test_build_messages_contains_rules_and_lesson():
    playbook = get_playbook("AE")
    messages = build_messages(
        request_for("AE"),
        resolve_location("Addition"),
        playbook,
        [RetrievedLesson("chunk-1", "Lesson body about addition.", 0.7)],
    )

    system = messages[0]["content"]
    user = messages[1]["content"]

    assert "exactly 5 questions" in system
    assert "A) string" in system
    assert playbook.code.value in user
    assert playbook.prompt_directives[0] in user
    assert "Lesson body about addition." in user


def test_parse_questions_accepts_valid_payload():
    playbook = get_playbook("AE")
    questions, insight = _parse_questions(json.dumps(payload_for("AE")), playbook)

    assert len(questions) == 5
    assert [question.question_number for question in questions] == [1, 2, 3, 4, 5]
    assert insight == "Generated summary."


def test_parse_questions_rejects_wrong_count():
    playbook = get_playbook("AE")
    payload = payload_for("AE")
    payload["questions"].pop()

    with pytest.raises(QuizGenerationError, match="expected 5 questions"):
        _parse_questions(json.dumps(payload), playbook)


def test_parse_questions_rejects_word_cap_violation():
    playbook = get_playbook("AE")
    payload = payload_for("AE")
    payload["questions"][0]["question_text"] = " ".join(["word"] * 21)

    with pytest.raises(QuizGenerationError, match="exceeds"):
        _parse_questions(json.dumps(payload), playbook)


def test_parse_questions_rejects_duplicate_options():
    playbook = get_playbook("AE")
    payload = payload_for("AE")
    payload["questions"][0]["options"] = ["A) 1", "A) 1", "C) 3", "D) 4"]

    with pytest.raises(QuizGenerationError, match="schema validation failed"):
        _parse_questions(json.dumps(payload), playbook)


def test_generate_quiz_success(monkeypatch):
    payload = json.dumps(payload_for("AE"))
    monkeypatch.setattr(generative_ai, "_call_groq", lambda messages: payload)

    result = generate_quiz(
        request_for("AE"),
        resolve_location("Addition"),
        get_playbook("AE"),
        [RetrievedLesson("chunk-1", "Lesson body.")],
    )

    assert result.competency_band == "Approaching Expectation"
    assert result.strand == "Numbers - Addition"
    assert len(result.questions) == 5


def test_generate_quiz_retries_once(monkeypatch):
    valid = json.dumps(payload_for("AE"))
    responses = iter(["not json", valid])
    calls = []

    def fake_call(messages):
        calls.append(messages)
        return next(responses)

    monkeypatch.setattr(generative_ai, "_call_groq", fake_call)

    result = generate_quiz(
        request_for("AE"),
        resolve_location("Addition"),
        get_playbook("AE"),
        [RetrievedLesson("chunk-1", "Lesson body.")],
    )

    assert len(calls) == 2
    assert len(result.questions) == 5


def test_generate_quiz_falls_back_on_failure(monkeypatch):
    def fail(messages):
        raise RuntimeError("Groq unavailable")

    monkeypatch.setattr(generative_ai, "_call_groq", fail)

    result = generate_quiz(
        request_for("EE"),
        resolve_location("Subtraction"),
        get_playbook("EE"),
        [RetrievedLesson("chunk-1", "Lesson body.")],
    )

    assert result.competency_band == "Exceeding Expectation"
    assert len(result.questions) == 6
    assert result.teacher_insight_summary == get_playbook("EE").teacher_insight_template
