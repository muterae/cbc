"""
Embed the lesson chunks and upsert them into Pinecone.

What gets embedded
------------------
``embedding_text``, not ``text``. MiniLM truncates near 256 tokens, so embedding
the full 2,000-character chunk would drop the learning activities. ``text`` is
stored in metadata instead and used later when building the prompt.

Answer keys are skipped by default (``section="answers"``, ``indexable=false``):
they contain only answers and must never ground a generated quiz.

Index
-----
``cbc-curriculum-rag``, 384 dimensions, cosine metric, AWS us-east-1 serverless,
matching ``sentence-transformers/all-MiniLM-L6-v2``.

Usage
-----
    python generator/embed_curriculum.py --dry-run     # embed 3 chunks, no network
    python generator/embed_curriculum.py               # upsert all lesson chunks
    python generator/embed_curriculum.py --reset       # clear stale vectors first
    python generator/embed_curriculum.py --recreate    # delete and rebuild the index
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
CHUNKS_PATH = BASE_DIR / "output" / "teacher_guide_chunks.jsonl"

DEFAULT_INDEX = "cbc-curriculum-rag"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSION = 384
METRIC = "cosine"
CLOUD = "aws"
REGION = "us-east-1"
BATCH_SIZE = 64

log = logging.getLogger("embed")


def load_chunks(path: Path, include_answers: bool, limit: int | None) -> list[dict]:
    """Read the JSONL produced by chunk_curriculum.py."""
    if not path.exists():
        raise SystemExit(f"Chunk file not found: {path}\nRun: python generator/chunk_curriculum.py")

    chunks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        chunk = json.loads(line)
        if not include_answers and not chunk.get("indexable", True):
            continue
        if not chunk["embedding_text"].strip():
            log.warning("Skipping %s: empty embedding_text", chunk["chunk_id"])
            continue
        chunks.append(chunk)

    if limit:
        chunks = chunks[:limit]
    return chunks


def build_metadata(chunk: dict) -> dict:
    """Flat metadata stored beside each vector, used for filters and prompts."""
    return {
        "document": chunk["document"],
        "term": chunk["term"],
        "strand": chunk["strand"],
        "sub_strand": chunk["sub_strand"],
        "week": int(chunk["week"]),
        "lesson": int(chunk["lesson"]),
        "lesson_title": chunk["lesson_title"],
        "section": chunk["section"],
        "indexable": bool(chunk["indexable"]),
        "page_start": int(chunk["page_start"]),
        "page_end": int(chunk["page_end"]),
        "char_count": int(chunk["char_count"]),
        "text": chunk["text"],
    }


def ensure_index(pc: Pinecone, name: str, recreate: bool) -> None:
    """Create the index when missing, and refuse to write into a wrong-shaped one."""
    existing = {index.name for index in pc.list_indexes()}

    if name in existing and recreate:
        log.info("Deleting existing index '%s'", name)
        pc.delete_index(name)
        existing.discard(name)
        while name in {index.name for index in pc.list_indexes()}:
            time.sleep(1)

    if name not in existing:
        log.info(
            "Creating index '%s' (dimension=%d, metric=%s, %s/%s)",
            name, DIMENSION, METRIC, CLOUD, REGION,
        )
        pc.create_index(
            name=name,
            dimension=DIMENSION,
            metric=METRIC,
            spec=ServerlessSpec(cloud=CLOUD, region=REGION),
        )

    while True:
        description = pc.describe_index(name)
        if description.status.get("ready"):
            break
        log.info("Waiting for index '%s' to become ready...", name)
        time.sleep(2)

    actual = pc.describe_index(name).dimension
    if actual != DIMENSION:
        raise SystemExit(
            f"Index '{name}' has dimension {actual}, expected {DIMENSION}. "
            "Use --recreate or choose another --index."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Embed lesson chunks into Pinecone.")
    parser.add_argument("--chunks", type=Path, default=CHUNKS_PATH)
    parser.add_argument("--index", default=None, help=f"index name (default: {DEFAULT_INDEX})")
    parser.add_argument("--limit", type=int, default=None, help="embed only the first N chunks")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--include-answers", action="store_true", help="also embed answer keys")
    parser.add_argument("--reset", action="store_true", help="delete all vectors before upserting")
    parser.add_argument("--recreate", action="store_true", help="delete and rebuild the index")
    parser.add_argument("--dry-run", action="store_true", help="embed a few chunks, touch no index")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    load_dotenv()
    index_name = args.index or os.getenv("PINECONE_INDEX", DEFAULT_INDEX)

    chunks = load_chunks(args.chunks, args.include_answers, args.limit)
    if not chunks:
        raise SystemExit("No chunks to embed.")

    total_chars = sum(len(chunk["embedding_text"]) for chunk in chunks)
    log.info(
        "Loaded %d chunks (%s chars, mean %d) from %s",
        len(chunks), f"{total_chars:,}", total_chars // len(chunks), args.chunks.name,
    )

    log.info("Loading embedding model %s", MODEL_NAME)
    started = time.perf_counter()
    model = SentenceTransformer(MODEL_NAME)
    log.info("Model ready in %.1fs (dimension %d)", time.perf_counter() - started, model.get_sentence_embedding_dimension())

    if args.dry_run:
        sample = chunks[:3]
        vectors = model.encode(
            [chunk["embedding_text"] for chunk in sample],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        log.info("Dry run: embedded %d chunks, vector shape %s", len(sample), vectors.shape)
        for chunk, vector in zip(sample, vectors):
            log.info(
                "  %s | norm=%.4f | %s",
                chunk["chunk_id"], float((vector ** 2).sum() ** 0.5), chunk["lesson_title"],
            )
        return 0

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is not set in .env")

    pc = Pinecone(api_key=api_key)
    ensure_index(pc, index_name, args.recreate)
    index = pc.Index(index_name)

    if args.reset:
        log.info("Deleting all vectors in '%s'", index_name)
        index.delete(delete_all=True)
        time.sleep(1)

    upserted = 0
    started = time.perf_counter()

    for offset in range(0, len(chunks), args.batch_size):
        batch = chunks[offset:offset + args.batch_size]
        vectors = model.encode(
            [chunk["embedding_text"] for chunk in batch],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        payload = [
            {
                "id": chunk["chunk_id"],
                "values": vector.tolist(),
                "metadata": build_metadata(chunk),
            }
            for chunk, vector in zip(batch, vectors)
        ]
        index.upsert(vectors=payload)
        upserted += len(payload)
        log.info(
            "Upserted batch %d/%d (%d/%d vectors, %.1fs)",
            offset // args.batch_size + 1,
            (len(chunks) + args.batch_size - 1) // args.batch_size,
            upserted,
            len(chunks),
            time.perf_counter() - started,
        )

    stats = index.describe_index_stats()
    log.info(
        "Done: %d vectors upserted in %.1fs | index now holds %d",
        upserted, time.perf_counter() - started, stats.total_vector_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
