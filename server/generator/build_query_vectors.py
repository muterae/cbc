"""Precompute the embedding for every reachable retrieval query.

Why this exists
---------------
``retriever.build_query()`` is deterministic: the string it produces depends only
on ``(strand, sub_strand, band)``. ``resolve_location`` validates those against a
fixed vocabulary (3 strands, 14 sub-strands) and there are 4 bands, so the entire
query space is 18 location combinations x 4 bands = 72 strings.

Embedding them once and shipping the result as a lookup table keeps
``sentence-transformers`` / ``torch`` out of the deployed image. The import alone
costs ~413 MB and ~37 s, which is what pushed the cloud container over its memory
ceiling and produced the 502s.

Because the vectors are produced by the same model, with the same query string and
the same normalisation as the live path used to use, retrieval results are
identical to the previous implementation. No re-indexing of Pinecone is required.

Usage
-----
    python generator/build_query_vectors.py
    python generator/build_query_vectors.py --output path/to/query_vectors.json
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from array import array
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVER_DIR = BASE_DIR.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from retriever import MODEL_NAME, build_query  # noqa: E402
from services.band_playbook import Band  # noqa: E402
from services.curriculum import STRANDS  # noqa: E402

DEFAULT_OUTPUT = SERVER_DIR / "services" / "query_vectors.json"
DIMENSION = 384


def encode_vector(values) -> str:
    """Pack a float32 vector as little-endian bytes, then base64."""
    packed = array("f", (float(value) for value in values))
    if sys.byteorder != "little":
        packed.byteswap()
    return base64.b64encode(packed.tobytes()).decode("ascii")


def enumerate_locations() -> list[tuple[str | None, str | None]]:
    """Every (strand, sub_strand) pair ``resolve_location`` can produce."""
    locations: list[tuple[str | None, str | None]] = [(None, None)]
    for strand, sub_strands in STRANDS.items():
        locations.append((strand, None))
        for sub_strand in sub_strands:
            locations.append((strand, sub_strand))
    return locations


def build_queries() -> list[str]:
    queries = [
        build_query(strand, sub_strand, band.value)
        for strand, sub_strand in enumerate_locations()
        for band in Band
    ]
    # Stable order and no duplicates, so regenerating produces a clean diff.
    return sorted(dict.fromkeys(queries))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Embed every reachable retrieval query into a lookup table."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    queries = build_queries()
    print(f"Enumerated {len(queries)} unique query strings")

    from sentence_transformers import SentenceTransformer

    print(f"Loading {MODEL_NAME} (offline script only; not a runtime dependency)")
    model = SentenceTransformer(MODEL_NAME)
    dimension = model.get_embedding_dimension()
    if dimension != DIMENSION:
        raise SystemExit(f"Expected {DIMENSION} dimensions, got {dimension}")

    vectors = model.encode(
        queries,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    payload = {
        "model": MODEL_NAME,
        "dimension": DIMENSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(queries),
        "vectors": {
            query: encode_vector(vector) for query, vector in zip(queries, vectors)
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    size_kb = args.output.stat().st_size / 1024
    print(f"Wrote {len(queries)} vectors ({size_kb:.0f} KB) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
