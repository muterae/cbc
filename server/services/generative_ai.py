"""Groq-backed quiz generation with validation and a deterministic fallback."""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, ValidationError

from retriever import RetrievedLesson
from services.band_playbook import BandPlaybook, QuizItem, validate_quiz
from services.curriculum import CurriculumLocation
from services.fallback_quiz import build_fallback_quiz
from services.quiz import AdaptiveQuizRequest, QuizQuestion, QuizResponse

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
TEMPERATURE = 0.3
MAX_TOKENS = 2600
MAX_LESSON_CHARS = 1800
MAX_ATTEMPTS = 2

log = logging.getLogger(__name__)
_client: Groq | None = None


class QuizGenerationError(Exception):
    """Raised when the model output cannot be turned into a valid quiz."""


class GeneratedQuestion(QuizItem):
    question_number: int | None = None
    pedagogical_objective: str = ""


class GeneratedQuiz(BaseModel):
    questions: list[GeneratedQuestion]
    teacher_insight_summary: str = ""


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = Groq(api_key=api_key)
    return _client


def _format_lesson(lesson: RetrievedLesson, number: int) -> str:
    meta = lesson.metadata or {}
    title = meta.get("lesson_title") or meta.get("section") or lesson.chunk_id
    position = " ".join(
        part
        for part in (
            str(meta.get("term", "")),
            f"W{meta.get('week')}" if meta.get("week") else "",
            f"L{meta.get('lesson')}" if meta.get("lesson") else "",
        )
        if part
    )
    heading = f"[{number}] {lesson.chunk_id} | {title}"
    if position:
        heading += f" | {position}"
    return f"{heading}\n{lesson.text[:MAX_LESSON_CHARS]}"


def build_messages(
    request: AdaptiveQuizRequest,
    location: CurriculumLocation,
    playbook: BandPlaybook,
    lessons: list[RetrievedLesson],
) -> list[dict]:
    low, high = playbook.number_range
    example = json.dumps(
        playbook.example_item.model_dump(), ensure_ascii=False, indent=2
    )
    directives = "\n".join(f"- {rule}" for rule in playbook.prompt_directives)
    forbidden = "\n".join(f"- {rule}" for rule in playbook.forbidden)
    excerpts = "\n\n".join(
        _format_lesson(lesson, number)
        for number, lesson in enumerate(lessons, start=1)
    )

    system = f"""You write Grade 3 Kenyan CBC Mathematics quizzes.

Return ONLY a JSON object. No markdown, no code fences, no explanation.
The JSON shape must be:
{{
  "questions": [
    {{
      "question_text": "string",
      "options": ["A) string", "B) string", "C) string", "D) string"],
      "correct_answer": "A) string",
      "hint": "string",
      "pedagogical_objective": "string"
    }}
  ],
  "teacher_insight_summary": "string"
}}

Hard rules:
- Write exactly {playbook.question_count} questions.
- Every question has exactly 4 unique options, prefixed "A) ", "B) ", "C) " and "D) ".
- correct_answer must exactly match one of the options.
- Use only the curriculum excerpts and the band rules below.
- Keep each question at or under {playbook.max_question_words} words.
- Keep the language simple and suitable for a Grade 3 learner in Kenya.
"""

    user = f"""Requested strand: {location.display}
Competency band: {playbook.code.value} ({playbook.code.name})
Session type: {request.session_type}
Number range: {low} to {high}
Regrouping allowed: {"yes" if playbook.regrouping else "no"}
Maximum steps: {playbook.max_steps}
Maximum words per question: {playbook.max_question_words}

Band directives:
{directives}

Forbidden:
{forbidden}

Example item:
{example}

Curriculum excerpts:
{excerpts}

Create the quiz now."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_groq_json(messages: list[dict], max_tokens: int = MAX_TOKENS) -> str:
    """Call Groq in JSON mode and return the raw content."""
    response = _get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=TEMPERATURE,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    if not content:
        raise QuizGenerationError("model returned an empty response")
    return content


def _call_groq(messages: list[dict]) -> str:
    return call_groq_json(messages)


def _parse_questions(
    raw: str, playbook: BandPlaybook
) -> tuple[list[QuizQuestion], str]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise QuizGenerationError(f"invalid JSON: {exc}") from exc

    try:
        generated = GeneratedQuiz.model_validate(data)
    except ValidationError as exc:
        raise QuizGenerationError(f"schema validation failed: {exc}") from exc

    questions = [
        QuizQuestion(
            question_number=number,
            question_text=item.question_text.strip(),
            options=[option.strip() for option in item.options],
            correct_answer=item.correct_answer.strip(),
            hint=item.hint.strip(),
            pedagogical_objective=(
                item.pedagogical_objective.strip() or playbook.task_style
            ),
        )
        for number, item in enumerate(generated.questions, start=1)
    ]

    errors = validate_quiz(questions, playbook)
    if errors:
        raise QuizGenerationError("; ".join(errors))

    return questions, generated.teacher_insight_summary.strip()


def generate_quiz(
    request: AdaptiveQuizRequest,
    location: CurriculumLocation,
    playbook: BandPlaybook,
    lessons: list[RetrievedLesson],
) -> QuizResponse:
    """Call Groq, validate its JSON, retry once, then use the fallback bank."""
    messages = build_messages(request, location, playbook, lessons)
    last_error: Exception | None = None
    raw = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = _call_groq(messages)
            questions, insight = _parse_questions(raw, playbook)
            log.info(
                "Generated %d questions for %s / %s with %s",
                len(questions),
                location.display,
                playbook.code.name,
                GROQ_MODEL,
            )
            return QuizResponse(
                strand=location.display,
                competency_band=playbook.code.value,
                questions=questions,
                teacher_insight_summary=insight
                or playbook.teacher_insight_template,
            )
        except Exception as exc:  # noqa: BLE001 - retry or fall back
            last_error = exc
            log.warning("Quiz generation attempt %d failed: %s", attempt, exc)
            if attempt < MAX_ATTEMPTS:
                if raw:
                    messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous answer failed validation: {exc}. "
                            "Return corrected JSON only, following the schema "
                            "and band rules exactly."
                        ),
                    }
                )
                raw = ""

    log.error("Falling back to deterministic quiz: %s", last_error)
    return QuizResponse(
        strand=location.display,
        competency_band=playbook.code.value,
        questions=build_fallback_quiz(playbook),
        teacher_insight_summary=playbook.teacher_insight_template,
    )
