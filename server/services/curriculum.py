"""Resolve user-facing strand names to the corpus vocabulary."""

from __future__ import annotations

from dataclasses import dataclass

STRANDS: dict[str, tuple[str, ...]] = {
    "NUMBERS": (
        "NUMBER CONCEPT",
        "WHOLE NUMBERS",
        "FRACTIONS",
        "ADDITION",
        "SUBTRACTION",
        "MULTIPLICATION",
        "DIVISION",
    ),
    "MEASUREMENT": ("LENGTH", "MASS", "CAPACITY", "TIME", "MONEY"),
    "GEOMETRY": ("POSITION AND DIRECTION", "SHAPES"),
}

SUB_STRAND_TO_STRAND = {
    sub_strand: strand
    for strand, sub_strands in STRANDS.items()
    for sub_strand in sub_strands
}


@dataclass(frozen=True)
class CurriculumLocation:
    strand: str | None
    sub_strand: str | None
    display: str


def _normalise(value: str) -> str:
    text = value.strip().upper().replace("_", " ").replace("&", " AND ")
    return " ".join(text.split())


def _display(value: str) -> str:
    return value.title().replace(" And ", " and ")


def resolve_location(
    strand: str | None, sub_strand: str | None = None
) -> CurriculumLocation:
    """Accept a strand, a sub-strand, or ``Numbers - Addition``.

    ``Mathematics`` / ``Math`` means no strand filter; the retriever returns the
    best Grade 3 lessons across the whole corpus.
    """
    raw_strand = _normalise(strand) if strand else ""
    raw_sub = _normalise(sub_strand) if sub_strand else ""

    if raw_strand in {"", "MATH", "MATHEMATICS"}:
        if raw_sub:
            if raw_sub not in SUB_STRAND_TO_STRAND:
                raise ValueError(f"Unknown sub-strand '{sub_strand}'.")
            top = SUB_STRAND_TO_STRAND[raw_sub]
            return CurriculumLocation(top, raw_sub, f"{_display(top)} - {_display(raw_sub)}")
        return CurriculumLocation(None, None, "Mathematics")

    top: str | None = None
    sub: str | None = None

    if "-" in raw_strand:
        left, right = raw_strand.split("-", 1)
        left, right = left.strip(), right.strip()
        if left and right:
            top, sub = left, right
        else:
            raise ValueError(f"Invalid strand '{strand}'.")
    elif raw_strand in STRANDS:
        top = raw_strand
    elif raw_strand in SUB_STRAND_TO_STRAND:
        top = SUB_STRAND_TO_STRAND[raw_strand]
        sub = raw_strand
    else:
        raise ValueError(
            f"Unknown strand '{strand}'. Use one of {', '.join(STRANDS)} "
            "or a sub-strand such as Addition."
        )

    if top not in STRANDS:
        raise ValueError(f"Unknown strand '{top}'. Use one of {', '.join(STRANDS)}.")

    if raw_sub:
        if sub and raw_sub != sub:
            raise ValueError(
                f"Strand '{strand}' already names sub-strand '{_display(sub)}'; "
                f"it conflicts with '{sub_strand}'."
            )
        sub = raw_sub

    if sub and sub not in STRANDS[top]:
        raise ValueError(
            f"Sub-strand '{sub}' does not belong to {_display(top)}. "
            f"Choose one of: {', '.join(STRANDS[top])}."
        )

    display = _display(top) if not sub else f"{_display(top)} - {_display(sub)}"
    return CurriculumLocation(top, sub, display)
