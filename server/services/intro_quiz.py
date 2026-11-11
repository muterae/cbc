"""Static baseline/placement quiz generated once from the curriculum.

The quiz is intentionally identical for every learner. It spans all four CBC
bands and the three Grade 3 strands. The endpoint serves a public view without
answer keys; the full quiz stays on the server for scoring.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from retriever import RetrievedLesson, retrieve_lessons
from services.band_playbook import Band, QuizItem, get_playbook, validate_item
from services.fallback_quiz import build_fallback_quiz
from services.generative_ai import call_groq_json

SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[1] / "generator" / "output" / "intro_quiz.json"
)
INTRO_QUIZ_ID = "intro-v1"
INTRO_QUIZ_VERSION = 1
INTRO_TITLE = "Grade 3 baseline quiz"
QUESTIONS_PER_BAND = 3
MAX_LESSON_CHARS = 1800

log = logging.getLogger(__name__)

TARGETS: dict[Band, list[tuple[str, str]]] = {
    Band.BE: [
        ("NUMBERS", "NUMBER CONCEPT"),
        ("NUMBERS", "WHOLE NUMBERS"),
        ("GEOMETRY", "SHAPES"),
    ],
    Band.AE: [
        ("NUMBERS", "ADDITION"),
        ("NUMBERS", "SUBTRACTION"),
        ("GEOMETRY", "SHAPES"),
    ],
    Band.ME: [
        ("NUMBERS", "ADDITION"),
        ("MEASUREMENT", "MONEY"),
        ("NUMBERS", "FRACTIONS"),
    ],
    Band.EE: [
        ("NUMBERS", "SUBTRACTION"),
        ("NUMBERS", "MULTIPLICATION"),
        ("MEASUREMENT", "MONEY"),
    ],
}

# (bank index, strand, sub-strand) used when a band cannot be generated.
FALLBACK_SPECS: dict[Band, list[tuple[int, str, str]]] = {
    Band.BE: [
        (0, "NUMBERS", "NUMBER CONCEPT"),
        (1, "NUMBERS", "NUMBER CONCEPT"),
        (2, "NUMBERS", "WHOLE NUMBERS"),
    ],
    Band.AE: [
        (0, "NUMBERS", "ADDITION"),
        (2, "NUMBERS", "SUBTRACTION"),
        (4, "GEOMETRY", "SHAPES"),
    ],
    Band.ME: [
        (0, "MEASUREMENT", "MONEY"),
        (3, "NUMBERS", "FRACTIONS"),
        (4, "MEASUREMENT", "MONEY"),
    ],
    Band.EE: [
        (0, "NUMBERS", "SUBTRACTION"),
        (1, "NUMBERS", "MULTIPLICATION"),
        (5, "NUMBERS", "MULTIPLICATION"),
    ],
}


class IntroQuestion(QuizItem):
    question_number: int = Field(ge=1)
    band: Band
    strand: str = Field(min_length=1)
    sub_strand: str = Field(min_length=1)
    pedagogical_objective: str = Field(min_length=1)


class IntroQuiz(BaseModel):
    quiz_id: str = INTRO_QUIZ_ID
    version: int = INTRO_QUIZ_VERSION
    title: str = INTRO_TITLE
    generated_at: str
    source: Literal["rag", "mixed", "fallback"] = "rag"
    questions: list[IntroQuestion]


class IntroQuizQuestion(BaseModel):
    question_number: int
    question_text: str
    options: list[str]
    band: str
    strand: str
    sub_strand: str
    pedagogical_objective: str


class IntroQuizResponse(BaseModel):
    quiz_id: str
    version: int
    title: str
    question_count: int
    generated_at: str
    source: str
    questions: list[IntroQuizQuestion]


class _GeneratedItem(QuizItem):
    strand: str = ""
    sub_strand: str = ""
    pedagogical_objective: str = ""


class _GeneratedBand(BaseModel):
    questions: list[_GeneratedItem]


_cache_lock = threading.RLock()
_cached_quiz: IntroQuiz | None = None


def _title(value: str) -> str:
    return value.title().replace(" And ", " and ")


def _normalise_label(value: str) -> str:
    return " ".join(
        value.replace("-", " ").replace("_", " ").split()
    ).casefold()


def _format_lesson(lesson: RetrievedLesson, number: int) -> str:
    meta = lesson.metadata or {}
    title = meta.get("lesson_title") or meta.get("section") or lesson.chunk_id
    return f"[{number}] {lesson.chunk_id} | {title}\n{lesson.text[:MAX_LESSON_CHARS]}"


def validate_intro_quiz(quiz: IntroQuiz) -> list[str]:
    """Return structural errors for the full placement quiz."""
    errors: list[str] = []
    if quiz.quiz_id != INTRO_QUIZ_ID:
        errors.append(f"expected quiz_id {INTRO_QUIZ_ID}, got {quiz.quiz_id}")
    if quiz.version != INTRO_QUIZ_VERSION:
        errors.append(f"expected version {INTRO_QUIZ_VERSION}, got {quiz.version}")
    if len(quiz.questions) != QUESTIONS_PER_BAND * len(Band):
        errors.append(
            f"expected {QUESTIONS_PER_BAND * len(Band)} questions, "
            f"got {len(quiz.questions)}"
        )

    expected_numbers = list(range(1, len(quiz.questions) + 1))
    actual_numbers = [question.question_number for question in quiz.questions]
    if actual_numbers != expected_numbers:
        errors.append("question_number values must be sequential from 1")

    counts = {band.name: 0 for band in Band}
    seen: set[str] = set()
    for question in quiz.questions:
        counts[question.band.name] += 1
        errors.extend(
            f"Q{question.question_number}: {error}"
            for error in validate_item(question, question.band)
        )
        key = question.question_text.strip().casefold()
        if key in seen:
            errors.append(f"Q{question.question_number}: duplicate question text")
        seen.add(key)

    for band, count in counts.items():
        if count != QUESTIONS_PER_BAND:
            errors.append(
                f"expected {QUESTIONS_PER_BAND} questions for {band}, got {count}"
            )

    return errors


def _load_snapshot() -> IntroQuiz | None:
    if not SNAPSHOT_PATH.exists():
        return None
    try:
        data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        quiz = IntroQuiz.model_validate(data)
        errors = validate_intro_quiz(quiz)
        if errors:
            raise ValueError("; ".join(errors))
        log.info("Loaded intro quiz snapshot from %s", SNAPSHOT_PATH)
        return quiz
    except Exception as exc:  # noqa: BLE001 - regenerate on a bad snapshot
        log.warning("Ignoring invalid intro quiz snapshot: %s", exc)
        return None


def save_snapshot(quiz: IntroQuiz) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(quiz.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _fallback_band(band: Band) -> list[IntroQuestion]:
    playbook = get_playbook(band)
    bank = build_fallback_quiz(playbook)
    questions = []
    for number, (index, strand, sub_strand) in enumerate(
        FALLBACK_SPECS[band], start=1
    ):
        item = bank[index]
        questions.append(
            IntroQuestion(
                question_number=number,
                band=band,
                strand=_title(strand),
                sub_strand=_title(sub_strand),
                question_text=item.question_text,
                options=item.options,
                correct_answer=item.correct_answer,
                hint=item.hint,
                pedagogical_objective=playbook.task_style,
            )
        )
    return questions


def _build_band_messages(
    band: Band, targets: list[tuple[str, str]], lessons: list[RetrievedLesson]
) -> list[dict]:
    playbook = get_playbook(band)
    target_lines = "\n".join(
        f"{number}. {_title(strand)} - {_title(sub_strand)}"
        for number, (strand, sub_strand) in enumerate(targets, start=1)
    )
    directives = "\n".join(f"- {rule}" for rule in playbook.prompt_directives)
    forbidden = "\n".join(f"- {rule}" for rule in playbook.forbidden)
    example = json.dumps(
        playbook.example_item.model_dump(), ensure_ascii=False, indent=2
    )
    excerpts = "\n\n".join(
        _format_lesson(lesson, number)
        for number, lesson in enumerate(lessons, start=1)
    )

    system = f"""You write one section of a fixed Grade 3 Kenyan CBC Mathematics placement quiz.

Return ONLY a JSON object. No markdown, no code fences, no explanation.
The JSON shape must be:
{{
  "questions": [
    {{
      "strand": "string",
      "sub_strand": "string",
      "question_text": "string",
      "options": ["A) string", "B) string", "C) string", "D) string"],
      "correct_answer": "A) string",
      "hint": "string",
      "pedagogical_objective": "string"
    }}
  ]
}}

Hard rules:
- Write exactly 3 questions for the {band.value} band.
- Question 1 targets target 1, question 2 targets target 2, question 3 targets target 3.
- Each question's "strand" and "sub_strand" must exactly match its target.
- Every question has exactly 4 unique options, prefixed "A) ", "B) ", "C) " and "D) ".
- correct_answer must exactly match one of the options.
- Keep each question at or under {playbook.max_question_words} words.
- Use only the curriculum excerpts and the band rules below.
- Keep the language simple and suitable for a Grade 3 learner in Kenya.
"""

    user = f"""Band: {band.value} ({band.name})
Targets:
{target_lines}

Band directives:
{directives}

Forbidden:
{forbidden}

Example item:
{example}

Curriculum excerpts:
{excerpts}

Create the 3 questions now."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _generate_band_questions(band: Band) -> list[IntroQuestion]:
    playbook = get_playbook(band)
    targets = TARGETS[band]

    lesson_map: dict[str, RetrievedLesson] = {}
    for strand, sub_strand in targets:
        for lesson in retrieve_lessons(strand, sub_strand, band.value, top_k=2):
            lesson_map.setdefault(lesson.chunk_id, lesson)
    lessons = list(lesson_map.values())

    messages = _build_band_messages(band, targets, lessons)
    last_error: Exception | None = None
    raw = ""

    for attempt in range(2):
        try:
            raw = call_groq_json(messages, max_tokens=1400)
            data = json.loads(raw)
            generated = _GeneratedBand.model_validate(data)
            if len(generated.questions) != QUESTIONS_PER_BAND:
                raise ValueError(
                    f"expected {QUESTIONS_PER_BAND} questions, "
                    f"got {len(generated.questions)}"
                )

            questions = []
            for number, (item, (strand, sub_strand)) in enumerate(
                zip(generated.questions, targets), start=1
            ):
                if not item.sub_strand:
                    raise ValueError(
                        f"question {number} is missing strand and sub_strand"
                    )
                if _normalise_label(item.sub_strand) != _normalise_label(sub_strand):
                    raise ValueError(
                        f"question {number} targets {item.sub_strand!r}, "
                        f"expected {sub_strand!r}"
                    )
                if item.strand and _normalise_label(item.strand) != _normalise_label(
                    strand
                ):
                    raise ValueError(
                        f"question {number} uses strand {item.strand!r}, "
                        f"expected {strand!r}"
                    )
                question = IntroQuestion(
                    question_number=number,
                    band=band,
                    strand=_title(strand),
                    sub_strand=_title(sub_strand),
                    question_text=item.question_text.strip(),
                    options=[option.strip() for option in item.options],
                    correct_answer=item.correct_answer.strip(),
                    hint=item.hint.strip(),
                    pedagogical_objective=(
                        item.pedagogical_objective.strip() or playbook.task_style
                    ),
                )
                errors = validate_item(question, playbook)
                if errors:
                    raise ValueError("; ".join(errors))
                questions.append(question)
            return questions
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = exc
            log.warning("Intro quiz generation failed for %s: %s", band.value, exc)
            if attempt == 0:
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

    raise RuntimeError(f"Could not generate {band.value}: {last_error}")


def generate_intro_quiz() -> IntroQuiz:
    """Generate a fresh quiz, falling back per band when the model fails."""
    questions: list[IntroQuestion] = []
    used_fallback = False
    used_rag = False

    for band in Band:
        try:
            questions.extend(_generate_band_questions(band))
            used_rag = True
        except Exception as exc:  # noqa: BLE001 - fallback is the guardrail
            log.error("Falling back for %s: %s", band.value, exc)
            questions.extend(_fallback_band(band))
            used_fallback = True

    source: Literal["rag", "mixed", "fallback"]
    if used_fallback and used_rag:
        source = "mixed"
    elif used_fallback:
        source = "fallback"
    else:
        source = "rag"

    questions = [
        question.model_copy(update={"question_number": number})
        for number, question in enumerate(questions, start=1)
    ]
    quiz = IntroQuiz(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source=source,
        questions=questions,
    )
    errors = validate_intro_quiz(quiz)
    if errors:
        raise RuntimeError("; ".join(errors))
    return quiz


def get_intro_quiz() -> IntroQuiz:
    """Return the static quiz, loading a snapshot or generating once."""
    global _cached_quiz
    with _cache_lock:
        if _cached_quiz is None:
            _cached_quiz = _load_snapshot() or generate_intro_quiz()
        return _cached_quiz


def clear_intro_quiz_cache() -> None:
    global _cached_quiz
    with _cache_lock:
        _cached_quiz = None


def generate_and_save_snapshot() -> IntroQuiz:
    quiz = generate_intro_quiz()
    save_snapshot(quiz)
    global _cached_quiz
    with _cache_lock:
        _cached_quiz = quiz
    return quiz


def to_response(quiz: IntroQuiz) -> IntroQuizResponse:
    """Build the public view, deliberately excluding answers and hints."""
    return IntroQuizResponse(
        quiz_id=quiz.quiz_id,
        version=quiz.version,
        title=quiz.title,
        question_count=len(quiz.questions),
        generated_at=quiz.generated_at,
        source=quiz.source,
        questions=[
            IntroQuizQuestion(
                question_number=question.question_number,
                question_text=question.question_text,
                options=question.options,
                band=question.band.value,
                strand=question.strand,
                sub_strand=question.sub_strand,
                pedagogical_objective=question.pedagogical_objective,
            )
            for question in quiz.questions
        ],
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = generate_and_save_snapshot()
    print(
        f"Wrote {SNAPSHOT_PATH} "
        f"({len(result.questions)} questions, source={result.source})"
    )
