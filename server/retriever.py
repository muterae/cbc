"""Curriculum retrieval from the Pinecone corpus.

The retriever embeds the same query shape used by ``generator/test_retrieval.py``
and always filters on ``indexable``. A strand and sub-strand filter is applied
when known, because Numbers has 102 lessons against 7 for Geometry.

If Pinecone or the embedding model is unavailable, a small static guidance
record is returned so quiz generation can still run.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

DEFAULT_INDEX = "cbc-curriculum-rag"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 3

log = logging.getLogger(__name__)

_model = None
_index = None


@dataclass(frozen=True)
class RetrievedLesson:
    chunk_id: str
    text: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


STATIC_GUIDANCE = {
    "NUMBERS": (
        "Grade 3 Numbers covers number concept, whole numbers, fractions, addition, "
        "subtraction, multiplication and division. Use counters, number lines, place "
        "value and familiar Kenyan objects."
    ),
    "MEASUREMENT": (
        "Grade 3 Measurement covers length, mass, capacity, time and money. Use rulers, "
        "balances, containers, clocks and shop contexts with shillings."
    ),
    "GEOMETRY": (
        "Grade 3 Geometry covers position and direction, and shapes. Use turns, lines, "
        "and named two-dimensional shapes."
    ),
    None: (
        "Grade 3 Mathematics covers Numbers, Measurement and Geometry. Use KICD "
        "Grade 3 outcomes and familiar Kenyan contexts."
    ),
}


def build_query(strand: str | None, sub_strand: str | None, band: str) -> str:
    return (
        f"Grade 3 Mathematics strand: {strand or 'all'}, "
        f"sub-strand: {sub_strand or 'all'}, assessment level: {band}."
    )


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        log.info("Loading embedding model %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_index():
    global _index
    if _index is None:
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY is not set")
        name = os.getenv("PINECONE_INDEX", DEFAULT_INDEX)
        _index = Pinecone(api_key=api_key).Index(name)
    return _index


def _fallback(strand: str | None, reason: str) -> list[RetrievedLesson]:
    log.warning("Using static curriculum guidance (%s)", reason)
    text = STATIC_GUIDANCE.get(strand, STATIC_GUIDANCE[None])
    return [
        RetrievedLesson(
            chunk_id=f"fallback-{strand or 'mathematics'}",
            text=text,
            metadata={"section": "fallback", "indexable": False},
        )
    ]


def retrieve_lessons(
    strand: str | None,
    sub_strand: str | None,
    band: str,
    top_k: int = TOP_K,
) -> list[RetrievedLesson]:
    """Return the top matching lessons, or static guidance on failure."""
    filters: dict = {"indexable": True}
    if strand:
        filters["strand"] = {"$eq": strand}
    if sub_strand:
        filters["sub_strand"] = {"$eq": sub_strand}

    query = build_query(strand, sub_strand, band)

    try:
        vector = _get_model().encode([query], normalize_embeddings=True)[0].tolist()
        result = _get_index().query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filters,
        )
    except Exception as exc:  # noqa: BLE001 - guardrail: never fail the request
        return _fallback(strand, f"{type(exc).__name__}: {exc}")

    lessons = []
    for match in result.matches:
        metadata = match.metadata or {}
        text = str(metadata.get("text", "")).strip()
        if not text:
            continue
        lessons.append(
            RetrievedLesson(
                chunk_id=match.id,
                text=text,
                score=float(match.score),
                metadata=metadata,
            )
        )

    if not lessons:
        return _fallback(strand, "no matching lessons")

    log.info(
        "Retrieved %d lesson(s) for %s / %s: %s",
        len(lessons),
        strand or "all",
        sub_strand or "all",
        ", ".join(lesson.chunk_id for lesson in lessons),
    )
    return lessons
