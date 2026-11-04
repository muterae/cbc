"""
Extract text from the curriculum PDFs into plain-text files for the RAG index.

Design goals
------------
* ``get_documents()`` is the single source of truth for *which* files are ingested.
  ``ingest_document()`` always receives a path returned by it, so adding a PDF to
  ``generator/documents`` is the only step needed to include it.
* One function does one file. The loop in ``main()`` only handles logging,
  skipping and error isolation.
* Every run logs the file being processed and its metadata (size, pages, hash,
  character count, output path) so extraction problems are visible immediately.
* Pages are joined with a form-feed (``\\f``), the standard page separator, so
  downstream chunking can recover page numbers by splitting on it.
* Files with no text layer are reported as ``EMPTY`` instead of silently writing
  an empty file.

Excluded
--------
``HI MATHEMATICS GRADE 2.pdf`` is a scanned document with no text layer and is
out of scope for this ingestion. It stays in ``EXCLUDED_DOCUMENTS`` so the
reason is documented rather than hidden.

Usage
-----
    python generator/ingest_documents.py
    python generator/ingest_documents.py --force
    python generator/ingest_documents.py --documents-dir other/ --output-dir other-out/
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
OUTPUT_DIR = BASE_DIR / "output"

# PDFs that must not be ingested, with the reason kept next to them.
EXCLUDED_DOCUMENTS = {
    "HI MATHEMATICS GRADE 2.pdf": "scanned images only, no text layer, out of scope",
}

PAGE_SEPARATOR = "\f"

log = logging.getLogger("ingest")

# pypdf emits a WARNING per embedded CFF font when fontTools is absent. The text
# still extracts correctly, so the noise is dropped and real errors still surface.
logging.getLogger("pypdf").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def get_documents(
    documents_dir: Path | str = DOCUMENTS_DIR,
    exclude: dict[str, str] | None = None,
) -> list[Path]:
    """Return every PDF in ``documents_dir`` except the excluded ones.

    This is the only function that decides what gets ingested. ``ingest_document``
    accepts any path returned here, so the two always stay compatible.
    """
    documents_dir = Path(documents_dir)
    exclude = EXCLUDED_DOCUMENTS if exclude is None else exclude

    if not documents_dir.is_dir():
        raise FileNotFoundError(f"Documents directory does not exist: {documents_dir}")

    documents = []
    for path in sorted(documents_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        if path.name in exclude:
            log.info("SKIP     %s (%s)", path.name, exclude[path.name])
            continue
        documents.append(path)

    if not documents:
        raise FileNotFoundError(f"No ingestible PDFs found in {documents_dir}")

    return documents


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------
def human_size(size_bytes: int) -> str:
    """Turn a byte count into a short readable string."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:,.1f} {unit}" if unit != "B" else f"{int(size):,} B"
        size /= 1024
    return f"{size:,.1f} GB"


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash the file in chunks so large PDFs do not load into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_metadata(path: Path) -> dict:
    """Metadata that describes the source file, independent of its content."""
    stat = path.stat()
    return {
        "file_name": path.name,
        "path": str(path),
        "size_bytes": stat.st_size,
        "size_human": human_size(stat.st_size),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "sha256": file_sha256(path),
    }


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
@dataclass
class IngestResult:
    """Everything produced for one document."""

    metadata: dict = field(default_factory=dict)
    status: str = "ok"  # ok | empty | skipped | failed
    reason: str = ""
    pages: int = 0
    characters: int = 0
    empty_pages: int = 0
    bad_characters: int = 0
    output_path: str = ""
    seconds: float = 0.0


def existing_page_count(path: Path) -> int:
    """Page count without extracting text, used when a file is skipped."""
    try:
        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001 - a broken PDF is reported as 0 pages
        return 0


def extract_pages(path: Path) -> tuple[list[str], int]:
    """Extract text page by page.

    Returns the page texts and the number of pages whose extraction raised an
    error. A single broken page does not abort the document.
    """
    reader = PdfReader(str(path))
    pages: list[str] = []
    failed_pages = 0
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - pypdf raises many different errors
            pages.append("")
            failed_pages += 1
    return pages, failed_pages


def ingest_document(
    document_path: Path | str,
    output_dir: Path | str = OUTPUT_DIR,
    force: bool = False,
) -> IngestResult:
    """Extract one PDF and write ``<name>.txt``.

    Always takes a path returned by :func:`get_documents`.

    Behaviour:
      1. Collects file metadata (name, size, modified date, SHA-256).
      2. Skips the file when a newer ``.txt`` already exists, unless ``force``.
      3. Extracts page text, tolerating individual page failures.
      4. Counts characters, empty pages and replacement characters.
      5. Writes UTF-8 text with ``\\f`` page separators.
      6. Returns an :class:`IngestResult` with status ``ok``, ``empty``,
         ``skipped`` or ``failed``.
    """
    started = time.perf_counter()
    document_path = Path(document_path)
    output_dir = Path(output_dir)
    result = IngestResult(metadata=collect_metadata(document_path))

    output_path = output_dir / f"{document_path.name}.txt"
    result.output_path = str(output_path)

    # ---- Skip when nothing changed -------------------------------------
    if (
        not force
        and output_path.exists()
        and output_path.stat().st_mtime >= document_path.stat().st_mtime
    ):
        result.status = "skipped"
        result.reason = "output is newer than the source PDF (use --force to redo)"
        result.pages = existing_page_count(document_path)
        result.characters = len(output_path.read_text(encoding="utf-8"))
        result.seconds = time.perf_counter() - started
        return result

    # ---- Extract --------------------------------------------------------
    try:
        pages, failed_pages = extract_pages(document_path)
    except Exception as error:  # noqa: BLE001 - report and continue with next file
        result.status = "failed"
        result.reason = f"{type(error).__name__}: {error}"
        result.seconds = time.perf_counter() - started
        return result

    result.pages = len(pages)
    result.characters = sum(len(text) for text in pages)
    result.empty_pages = sum(1 for text in pages if len(text.strip()) < 20)
    result.bad_characters = sum(text.count("\ufffd") for text in pages)

    text = f"\n{PAGE_SEPARATOR}\n".join(page.rstrip() for page in pages)

    if not text.strip():
        result.status = "empty"
        result.reason = "no text layer found (scanned document?)"
        result.seconds = time.perf_counter() - started
        return result

    if failed_pages:
        result.reason = f"{failed_pages} page(s) failed to extract"

    # ---- Write ----------------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8", newline="\n")

    result.seconds = time.perf_counter() - started
    return result


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log_header(index: int, total: int, path: Path) -> None:
    """Announce the file currently being ingested."""
    log.info("[%d/%d] INGESTING  %s", index, total, path.name)


def log_details(result: IngestResult) -> None:
    """Print the metadata block for one document."""
    meta = result.metadata
    rows = [
        ("path", meta["path"]),
        ("size", f"{meta['size_human']} ({meta['size_bytes']:,} bytes)"),
        ("modified", meta["modified_at"]),
        ("sha256", meta["sha256"][:16] + "..."),
        ("pages", f"{result.pages:,}"),
    ]

    if result.status in {"ok", "empty", "failed", "skipped"}:
        rows.append(("text", f"{result.characters:,} chars"))
    if result.status in {"ok", "empty", "failed"}:
        rows.append(("quality", f"{result.empty_pages} empty page(s), "
                                f"{result.bad_characters} bad char(s)"))

    if result.output_path:
        rows.append(("output", result.output_path))

    status_line = result.status.upper()
    if result.reason:
        status_line += f" - {result.reason}"
    status_line += f" ({result.seconds:.1f}s)"
    rows.append(("status", status_line))

    for key, value in rows:
        log.info("        %-9s %s", key + ":", value)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract curriculum PDFs to text.")
    parser.add_argument("--documents-dir", type=Path, default=DOCUMENTS_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--force", action="store_true", help="re-extract even if output is current")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    documents = get_documents(args.documents_dir)
    log.info("Found %d document(s) to ingest", len(documents))

    counts = {"ok": 0, "empty": 0, "skipped": 0, "failed": 0}

    for index, path in enumerate(documents, start=1):
        log_header(index, len(documents), path)
        result = ingest_document(path, output_dir=args.output_dir, force=args.force)
        log_details(result)
        counts[result.status] += 1

    log.info(
        "Finished: %d ingested, %d skipped, %d empty, %d failed",
        counts["ok"],
        counts["skipped"],
        counts["empty"],
        counts["failed"],
    )
    return 1 if counts["failed"] or counts["empty"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
