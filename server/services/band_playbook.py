"""CBC competency band -> question-difficulty playbook.

This module is the single source of truth for how each CBC band shapes a quiz:
item count, number range, regrouping, cognitive demand, language limits, hint
style, distractor policy and few-shot examples.

The band fixes the difficulty ceiling. The retrieved KICD lesson supplies the
skill. The prompt builder combines both.

Note: the four bands come from the project specification (AGENTS.md); the CBA
PDF in the corpus explains assessment policy, not band difficulty descriptors.
This is therefore a project design artifact, not an official KICD difficulty
scale.
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

DOCS_PATH = Path(__file__).resolve().parents[1] / "docs" / "band-playbook.md"


class Band(StrEnum):
    BE = "Below Expectation"
    AE = "Approaching Expectation"
    ME = "Meeting Expectation"
    EE = "Exceeding Expectation"


class QuizItem(BaseModel):
    """A single four-option item in the shape the mobile client expects."""

    question_text: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    hint: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_options(self) -> "QuizItem":
        if len(set(self.options)) != 4:
            raise ValueError("options must be unique")
        if self.correct_answer not in self.options:
            raise ValueError("correct_answer must be one of options")
        return self


class BandPlaybook(BaseModel):
    code: Band
    rank: int = Field(ge=1, le=4)
    question_count: int = Field(ge=1)
    max_question_words: int = Field(ge=1)
    number_range: tuple[int, int]
    regrouping: bool
    max_steps: int = Field(ge=1)
    cognitive_level: str
    task_style: str
    context_style: str
    hint_style: str
    distractor_policy: str
    description: str
    prompt_directives: list[str] = Field(min_length=1)
    forbidden: list[str] = Field(min_length=1)
    teacher_insight_template: str
    example_item: QuizItem

    @field_validator("number_range")
    @classmethod
    def check_range(cls, value: tuple[int, int]) -> tuple[int, int]:
        low, high = value
        if low < 0 or high < low:
            raise ValueError("number_range must be non-negative and ordered")
        return value


BAND_PLAYBOOK: dict[Band, BandPlaybook] = {
    Band.BE: BandPlaybook(
        code=Band.BE,
        rank=1,
        question_count=4,
        max_question_words=12,
        number_range=(0, 10),
        regrouping=False,
        max_steps=1,
        cognitive_level="Recognise and count with concrete support",
        task_style="Direct counting or matching with objects, pictures or counters.",
        context_style="Classroom counters, sticks, bottle tops and learners.",
        hint_style="Step-by-step physical action, e.g. touch each object while counting.",
        distractor_policy="Options visibly different in size; avoid near-misses.",
        description=(
            "Learner needs concrete support to recognise numbers and complete "
            "one-step counting tasks."
        ),
        prompt_directives=[
            "Use numbers from 0 to 10 only.",
            "Use concrete objects or pictures described in words.",
            "Ask one direct question with one action.",
            "Keep the question at or under 12 words.",
            "Make the correct option clearly different from the distractors.",
            "Give a hint that tells the learner exactly what to do physically.",
        ],
        forbidden=[
            "No carrying or borrowing (regrouping).",
            "No multi-step word problems.",
            "No missing-number or inverse reasoning.",
            "No abstract symbols without a concrete context.",
            "No negative numbers.",
        ],
        teacher_insight_template=(
            "Learner is practising counting and number recognition with "
            "concrete support."
        ),
        example_item=QuizItem(
            question_text="There are 4 mangoes. How many mangoes are there?",
            options=["A) 2", "B) 3", "C) 4", "D) 5"],
            correct_answer="C) 4",
            hint="Touch each mango as you count: one, two, three, four.",
        ),
    ),
    Band.AE: BandPlaybook(
        code=Band.AE,
        rank=2,
        question_count=5,
        max_question_words=20,
        number_range=(0, 20),
        regrouping=False,
        max_steps=1,
        cognitive_level="Apply one familiar procedure",
        task_style="One-step arithmetic or a short word problem with familiar realia.",
        context_style="Kenyan everyday objects: mangoes, shillings, sukuma wiki, pencils.",
        hint_style="Rule reminder, e.g. count on from the larger number.",
        distractor_policy="One off-by-one near-miss; the other options are clearly wrong.",
        description=(
            "Learner can apply a single familiar procedure with numbers up to 20 "
            "when the context is familiar."
        ),
        prompt_directives=[
            "Use numbers from 0 to 20 only.",
            "Use one operation and one step.",
            "Use familiar Kenyan objects or money.",
            "Do not require carrying or borrowing.",
            "Keep the question at or under 20 words.",
            "Include one near-miss distractor.",
        ],
        forbidden=[
            "No carrying or borrowing (regrouping).",
            "No multi-step word problems.",
            "No missing-number or inverse reasoning.",
            "No negative numbers.",
            "No unfamiliar or abstract contexts.",
        ],
        teacher_insight_template=(
            "Learner is applying single-step arithmetic in familiar everyday contexts."
        ),
        example_item=QuizItem(
            question_text=(
                "Amina has 12 mangoes. She buys 5 more. "
                "How many mangoes does she have now?"
            ),
            options=["A) 15", "B) 16", "C) 17", "D) 18"],
            correct_answer="C) 17",
            hint="Start at 12 and count 5 steps forward.",
        ),
    ),
    Band.ME: BandPlaybook(
        code=Band.ME,
        rank=3,
        question_count=5,
        max_question_words=30,
        number_range=(0, 100),
        regrouping=True,
        max_steps=2,
        cognitive_level="Apply standard Grade 3 procedures",
        task_style="KICD end-of-sub-strand tasks; one- and two-step word problems.",
        context_style="Familiar school and home contexts with Kenyan realia.",
        hint_style="Self-checking prompt, e.g. identify the operation and estimate the answer.",
        distractor_policy="Include a common misconception distractor, e.g. wrong operation or off-by-one.",
        description=(
            "Learner can apply Grade 3 KICD skills to standard one- and two-step tasks."
        ),
        prompt_directives=[
            "Use numbers from 0 to 100.",
            "Allow carrying and borrowing.",
            "Use one or two steps.",
            "Use a KICD-style word problem.",
            "Keep the question at or under 30 words.",
            "Include a distractor based on a common misconception.",
            "Hint should help the learner check the operation or estimate the answer.",
        ],
        forbidden=[
            "No inverse or missing-number reasoning.",
            "No more than two steps.",
            "No negative numbers.",
            "No ambiguous wording.",
            "No content beyond the Grade 3 KICD sub-strand.",
        ],
        teacher_insight_template=(
            "Learner is applying Grade 3 skills to standard one- and two-step tasks."
        ),
        example_item=QuizItem(
            question_text="A pencil costs 5 shillings. How much do 4 pencils cost?",
            options=["A) 9", "B) 15", "C) 20", "D) 25"],
            correct_answer="C) 20",
            hint="Multiply the cost of one pencil by the number of pencils. Check by adding 5 four times.",
        ),
    ),
    Band.EE: BandPlaybook(
        code=Band.EE,
        rank=4,
        question_count=6,
        max_question_words=40,
        number_range=(0, 100),
        regrouping=True,
        max_steps=3,
        cognitive_level="Analyse, reason and transfer",
        task_style=(
            "Inverse reasoning, missing-number or missing-operator problems, "
            "comparison and multi-step tasks."
        ),
        context_style="Less familiar or novel contexts that require transfer.",
        hint_style="Strategy nudge, e.g. work backwards or test each option.",
        distractor_policy="Include a near-miss based on the inverse error; all options plausible.",
        description=(
            "Learner can reason with inverse relationships, missing operators and "
            "multi-step problems."
        ),
        prompt_directives=[
            "Use numbers from 0 to 100.",
            "Allow carrying and borrowing.",
            "Include inverse reasoning, a missing number or operator, or a multi-step problem.",
            "Use a less familiar context to test transfer.",
            "Keep the question at or under 40 words.",
            "Include plausible distractors that reflect common reasoning errors.",
            "Hint should suggest a strategy, not the answer.",
        ],
        forbidden=[
            "No negative numbers.",
            "No algebra with letters.",
            "No content beyond the Grade 3 KICD sub-strand.",
            "No trick questions.",
            "No more than three steps.",
        ],
        teacher_insight_template=(
            "Learner is reasoning with inverse and multi-step problems and "
            "explaining their thinking."
        ),
        example_item=QuizItem(
            question_text="What number goes in the box? \u25a1 + 6 = 15",
            options=["A) 7", "B) 8", "C) 9", "D) 10"],
            correct_answer="C) 9",
            hint="Work backwards: subtract 6 from 15.",
        ),
    ),
}


def resolve_band(value: str | Band) -> Band:
    """Accept a code (BE), full label, or slug (below-expectation)."""
    if isinstance(value, Band):
        return value

    raw = value.strip()
    if not raw:
        raise ValueError("Band is empty.")

    code = raw.upper()
    if code in Band.__members__:
        return Band[code]

    folded = raw.casefold()
    for band in Band:
        if folded == band.value.casefold():
            return band

    slug = re.sub(r"[\s_-]+", "-", folded)
    for band in Band:
        if slug == re.sub(r"[\s_-]+", "-", band.value.casefold()):
            return band

    valid = ", ".join(band.value for band in Band)
    raise ValueError(f"Unknown band '{value}'. Use BE, AE, ME, EE or one of: {valid}.")


def get_playbook(band: str | Band) -> BandPlaybook:
    return BAND_PLAYBOOK[resolve_band(band)]


def list_playbooks() -> list[BandPlaybook]:
    return sorted(BAND_PLAYBOOK.values(), key=lambda playbook: playbook.rank)


_OPTION_PREFIX = re.compile(r"^[A-D]\) \S")


def validate_item(
    item: QuizItem, band: str | Band | BandPlaybook
) -> list[str]:
    """Return structural errors for one generated item. Empty list means valid."""
    playbook = band if isinstance(band, BandPlaybook) else get_playbook(band)
    errors: list[str] = []

    if len(item.options) != 4:
        errors.append(f"expected 4 options, got {len(item.options)}")
    if len(set(item.options)) != 4:
        errors.append("options must be unique")
    if item.correct_answer not in item.options:
        errors.append("correct_answer must be one of options")
    if not item.hint.strip():
        errors.append("hint must not be empty")

    words = len(re.findall(r"\S+", item.question_text))
    if words > playbook.max_question_words:
        errors.append(
            f"{words} words exceeds the {playbook.code} limit of "
            f"{playbook.max_question_words}"
        )

    for option in item.options:
        if not _OPTION_PREFIX.match(option):
            errors.append(f"option '{option}' must use the 'A) ...' format")

    return errors


def validate_quiz(
    items: list[QuizItem], band: str | Band | BandPlaybook
) -> list[str]:
    """Return structural errors for a whole quiz. Empty list means valid."""
    playbook = band if isinstance(band, BandPlaybook) else get_playbook(band)
    errors: list[str] = []

    if len(items) != playbook.question_count:
        errors.append(
            f"expected {playbook.question_count} questions for {playbook.code}, "
            f"got {len(items)}"
        )

    for number, item in enumerate(items, start=1):
        errors.extend(f"Q{number}: {error}" for error in validate_item(item, playbook))

    return errors


def render_markdown() -> str:
    """Render the human-readable companion document from the Python source."""
    lines = [
        "# CBC band playbook",
        "",
        "> Generated from `services/band_playbook.py`. Do not edit by hand.",
        "> Regenerate with `python -m services.band_playbook`.",
        "",
        "This table defines the difficulty ceiling for each CBC competency band.",
        "The retrieved KICD lesson supplies the skill; the band supplies the level.",
        "",
        "## Difficulty ladder",
        "",
        "| Band | Code | Rank | Questions | Numbers | Regrouping | Max steps | Max words |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for playbook in list_playbooks():
        low, high = playbook.number_range
        lines.append(
            f"| {playbook.code.value} | {playbook.code.name} | {playbook.rank} | "
            f"{playbook.question_count} | {low}-{high} | "
            f"{'Yes' if playbook.regrouping else 'No'} | "
            f"{playbook.max_steps} | {playbook.max_question_words} |"
        )

    for playbook in list_playbooks():
        lines.extend(
            [
                "",
                f"## {playbook.code.value} ({playbook.code.name})",
                "",
                playbook.description,
                "",
                "| Property | Value |",
                "|---|---|",
                f"| Cognitive level | {playbook.cognitive_level} |",
                f"| Task style | {playbook.task_style} |",
                f"| Context | {playbook.context_style} |",
                f"| Hint style | {playbook.hint_style} |",
                f"| Distractor policy | {playbook.distractor_policy} |",
                f"| Teacher insight | {playbook.teacher_insight_template} |",
                "",
                "### Prompt directives",
                "",
            ]
        )
        lines.extend(f"- {directive}" for directive in playbook.prompt_directives)
        lines.extend(["", "### Forbidden", ""])
        lines.extend(f"- {rule}" for rule in playbook.forbidden)

        item = playbook.example_item
        lines.extend(
            [
                "",
                "### Example item",
                "",
                f"**Question:** {item.question_text}",
                "",
            ]
        )
        lines.extend(f"- {option}" for option in item.options)
        lines.extend(
            [
                "",
                f"**Correct answer:** {item.correct_answer}",
                "",
                f"**Hint:** {item.hint}",
            ]
        )

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.write_text(render_markdown(), encoding="utf-8")
    print(f"Wrote {DOCS_PATH}")
