"""
Retrieval smoke test for the Pinecone corpus.

Runs a handful of band-shaped queries and prints the top matches, so the quality
of the index is visible before any generation code depends on it.

Usage
-----
    python generator/test_retrieval.py
    python generator/test_retrieval.py --top-k 3 --strand NUMBERS
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

DEFAULT_INDEX = "cbc-curriculum-rag"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

log = logging.getLogger("retrieval-test")

# Queries shaped the way the pipeline will shape them: band difficulty plus skill.
QUERIES = [
    {
        "band": "Below Expectation",
        "strand": "NUMBERS",
        "sub_strand": "NUMBER CONCEPT",
        "text": "identify the position of objects using ordinal numbers first to fifth, with counters",
    },
    {
        "band": "Approaching Expectation",
        "strand": "NUMBERS",
        "sub_strand": "ADDITION",
        "text": "add a two digit number and a one digit number using mangoes and shillings",
    },
    {
        "band": "Meeting Expectation",
        "strand": "NUMBERS",
        "sub_strand": "FRACTIONS",
        "text": "identify a quarter as part of a whole and share a chapati equally",
    },
    {
        "band": "Exceeding Expectation",
        "strand": "NUMBERS",
        "sub_strand": "SUBTRACTION",
        "text": "find the missing number in 15 minus what equals 7, reverse reasoning",
    },
    {
        "band": "Meeting Expectation",
        "strand": "MEASUREMENT",
        "sub_strand": "MONEY",
        "text": "work out change after buying goods in a shop",
    },
    {
        "band": "Approaching Expectation",
        "strand": "GEOMETRY",
        "sub_strand": "POSITION AND DIRECTION",
        "text": "move along a straight line and turn to the right or left",
    },
]


def build_query(query: dict) -> str:
    """Same query shape the retriever will use at inference time."""
    return (
        f"Grade 3 Mathematics strand: {query['strand']}, "
        f"sub-strand: {query['sub_strand']}, "
        f"assessment level: {query['band']}. {query['text']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the curriculum index.")
    parser.add_argument("--index", default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--strand", default=None, help="restrict a single query to one strand")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is not set in .env")

    index_name = args.index or os.getenv("PINECONE_INDEX", DEFAULT_INDEX)
    index = Pinecone(api_key=api_key).Index(index_name)

    stats = index.describe_index_stats()
    log.info("Index '%s' holds %d vectors", index_name, stats.total_vector_count)
    if stats.total_vector_count == 0:
        raise SystemExit("Index is empty. Run: python generator/embed_curriculum.py")

    log.info("Loading %s", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)

    queries = QUERIES
    if args.strand:
        queries = [q for q in queries if q["strand"] == args.strand.upper()]

    for query in queries:
        text = build_query(query)
        vector = model.encode([text], normalize_embeddings=True)[0].tolist()
        result = index.query(
            vector=vector,
            top_k=args.top_k,
            include_metadata=True,
            filter={
                "indexable": True,
                "sub_strand": {"$eq": query["sub_strand"]},
            },
        )

        print()
        print("=" * 78)
        print(f"{query['band']} | {query['strand']} | {query['sub_strand']}")
        print("=" * 78)
        for rank, match in enumerate(result.matches, start=1):
            meta = match.metadata or {}
            preview = " ".join(str(meta.get("text", ""))[:140].split())
            print(
                f"{rank}. score {match.score:.3f} | {meta.get('term')} | "
                f"{meta.get('sub_strand')} | W{meta.get('week')} L{meta.get('lesson')}"
            )
            print(f"   {meta.get('lesson_title')}  (p.{meta.get('page_start')}-{meta.get('page_end')})")
            print(f"   {preview}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
