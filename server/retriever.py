"""Curriculum retrieval from the Pinecone corpus.

The retriever embeds the same query shape used by ``generator/test_retrieval.py``
and always filters on ``indexable``. A strand and sub-strand filter is applied
when known, because Numbers has 102 lessons against 7 for Geometry.

Query embeddings are **precomputed**, not computed on the fly. The query string
is fully determined by ``(strand, sub_strand, band)`` and the vocabulary is
fixed, so ``generator/build_query_vectors.py`` embeds every reachable string once
and commits the result to ``services/query_vectors.json``. This keeps
``sentence-transformers`` and ``torch`` out of the deployed image, where the
import alone cost ~413 MB and ~37 s and caused the container to be OOM-killed.

If Pinecone or the vector cache is unavailable, a small static guidance record is
returned so quiz generation can still run.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import struct
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_INDEX = "cbc-curriculum-rag"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
QUERY_VECTORS_PATH = Path(__file__).resolve().parent / "services" / "query_vectors.json"
VECTOR_DIMENSION = 384
TOP_K = 3
QUERY_TIMEOUT = 10.0

log = logging.getLogger(__name__)

_query_vectors: dict[str, tuple[float, ...]] | None = None
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


def _band_label(band: str) -> str:
    """Accept a code (``ME``), slug, or full label; always return the full label.

    The precomputed cache is keyed by the full label, so normalising here means a
    caller passing ``"ME"`` still hits the cache instead of silently degrading to
    static guidance.
    """
    try:
        from services.band_playbook import resolve_band

        return resolve_band(band).value
    except (ImportError, ValueError):
        return band


def build_query(strand: str | None, sub_strand: str | None, band: str) -> str:
    return (
        f"Grade 3 Mathematics strand: {strand or 'all'}, "
        f"sub-strand: {sub_strand or 'all'}, assessment level: {_band_label(band)}."
    )


def load_query_vectors(path: Path | None = None) -> dict[str, tuple[float, ...]]:
    """Load the precomputed query embeddings into memory.

    The table is generated offline by ``generator/build_query_vectors.py`` using
    ``sentence-transformers/all-MiniLM-L6-v2`` with normalised vectors, which is
    exactly what the previous on-the-fly path produced.
    """
    global _query_vectors
    if _query_vectors is None:
        source = path or QUERY_VECTORS_PATH
        payload = json.loads(source.read_text(encoding="utf-8"))
        dimension = int(payload.get("dimension", VECTOR_DIMENSION))
        vectors: dict[str, tuple[float, ...]] = {}
        for query, encoded in payload["vectors"].items():
            vectors[query] = struct.unpack(f"<{dimension}f", base64.b64decode(encoded))
        _query_vectors = vectors
        log.info(
            "Loaded %d precomputed query vectors from %s", len(vectors), source.name
        )
    return _query_vectors


def embed_query(query: str) -> list[float] | None:
    """Return the cached embedding for a query string, or ``None`` when unknown."""
    try:
        vector = load_query_vectors().get(query)
    except (OSError, ValueError, KeyError) as exc:
        log.warning(
            "Query vector cache unavailable (%s: %s)", type(exc).__name__, exc
        )
        return None
    return list(vector) if vector else None


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

    vector = embed_query(query)
    if vector is None:
        return _fallback(strand, "query vector not precomputed")

    try:
        result = _get_index().query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter=filters,
            timeout=QUERY_TIMEOUT,
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
