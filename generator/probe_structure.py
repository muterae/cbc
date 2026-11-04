"""
Map the heading structure of the Grade 3 Mathematics Teacher's Guide.

Why this exists
---------------
The guide is a table-heavy document that repeats every sub-strand once per term:

    TERM ONE   -> NUMBERS / MEASUREMENT / GEOMETRY
    TERM TWO   -> NUMBERS / MEASUREMENT / GEOMETRY
    TERM THREE -> NUMBERS / MEASUREMENT / GEOMETRY

A fixed-size character splitter would cut a sub-strand away from its learning
outcomes and assessment criteria. This probe tells us exactly where each
sub-strand starts so the chunker can split on real headings.

A quirk worth knowing: the strand heading ("NUMBERS", "MEASUREMENT",
"GEOMETRY") is sometimes extracted at the *top* of a page and sometimes at the
*bottom*, even when the sub-strand heading is at the top. So the code does not
walk the text sequentially. It finds every heading first, then attaches each
sub-strand to whichever strand heading is nearest in the document.

Usage
-----
    python generator/probe_structure.py
    python generator/probe_structure.py --document "MATHEMATICS_PUPILS BOOK_ GRADE  3 22nd Dec.pdf"
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ingest_documents import DOCUMENTS_DIR, OUTPUT_DIR, PAGE_SEPARATOR, get_documents, ingest_document

log = logging.getLogger("probe")

TERM_PATTERN = re.compile(r"^TERM\s+(ONE|TWO|THREE)$", re.IGNORECASE)

# Major strand headings, printed in caps in the guide.
STRANDS = {"NUMBERS", "MEASUREMENT", "GEOMETRY"}

# All-caps lines that are page furniture, not headings.
STOPWORDS = {
    "NOT FOR SALE",
    "PROPERTY OF THE GOVERNMENT OF KENYA",
}

# A sub-strand heading is immediately followed by one of these markers.
SUBSTRAND_MARKERS = ("Time -", "Background Information")

# Expected sub-strand -> strand mapping, used only to flag anomalies.
EXPECTED_STRAND = {
    "NUMBER CONCEPT": "NUMBERS",
    "WHOLE NUMBERS": "NUMBERS",
    "FRACTIONS": "NUMBERS",
    "ADDITION": "NUMBERS",
    "SUBTRACTION": "NUMBERS",
    "MULTIPLICATION": "NUMBERS",
    "DIVISION": "NUMBERS",
    "LENGTH": "MEASUREMENT",
    "MASS": "MEASUREMENT",
    "CAPACITY": "MEASUREMENT",
    "TIME": "MEASUREMENT",
    "MONEY": "MEASUREMENT",
    "POSITION AND DIRECTION": "GEOMETRY",
    "SHAPES": "GEOMETRY",
}


@dataclass
class Heading:
    """A heading and its position in the flattened document."""

    index: int
    page: int
    text: str


@dataclass
class SubStrand:
    name: str
    page: int


@dataclass
class Strand:
    name: str
    page: int
    sub_strands: list[SubStrand] = field(default_factory=list)


@dataclass
class Term:
    name: str
    page: int
    strands: list[Strand] = field(default_factory=list)


def flatten_pages(pages: list[str]) -> list[tuple[int, str]]:
    """Turn pages into one ordered list of (page_number, non-empty_line)."""
    flat: list[tuple[int, str]] = []
    for page_number, text in enumerate(pages, start=1):
        for line in text.split("\n"):
            line = line.strip()
            if line:
                flat.append((page_number, line))
    return flat


def looks_like_heading(line: str) -> bool:
    """True for short, all-caps, mostly alphabetic lines such as 'NUMBER CONCEPT'."""
    if not (4 <= len(line) <= 42):
        return False
    if line in STOPWORDS or line in STRANDS or TERM_PATTERN.match(line):
        return False
    letters = re.sub(r"[^A-Za-z ]", "", line)
    if len(letters) < 4:
        return False
    return line == line.upper()


def find_headings(flat: list[tuple[int, str]]) -> tuple[list[Heading], list[Heading], list[Heading]]:
    """Return term, strand and sub-strand headings, each with a document position."""
    terms: list[Heading] = []
    strands: list[Heading] = []
    sub_strands: list[Heading] = []

    for index, (page, line) in enumerate(flat):
        if TERM_PATTERN.match(line):
            terms.append(Heading(index, page, line.upper()))
        elif line in STRANDS:
            strands.append(Heading(index, page, line))
        elif looks_like_heading(line):
            lookahead = " ".join(text for _, text in flat[index + 1:index + 5])
            if any(marker in lookahead for marker in SUBSTRAND_MARKERS):
                sub_strands.append(Heading(index, page, line))

    return terms, strands, sub_strands


def choose_strand(strands: list[Heading], sub: Heading) -> Heading | None:
    """Attach a sub-strand to its strand heading.

    Normally that is the last strand heading before it. When the heading is
    extracted at the bottom of the same page, it also covers the sub-strand
    printed above it, so a later same-page heading wins.
    """
    before = [s for s in strands if s.index < sub.index]
    chosen = before[-1] if before else None

    same_page_after = next(
        (s for s in strands if s.index > sub.index and s.page == sub.page),
        None,
    )
    return same_page_after or chosen


def build_outline(pages: list[str]) -> list[Term]:
    """Group sub-strands under their strand and term.

    Page numbers are 1-based and match the PDF viewer, not the printed folio.
    """
    flat = flatten_pages(pages)
    terms, strands, sub_strands = find_headings(flat)

    if not strands or not sub_strands:
        return []

    outline: dict[int, Term] = {}
    index_of: dict[tuple[int, str], Strand] = {}

    for sub in sub_strands:
        # A strand heading belongs to the sub-strands that follow it...
        strand_heading = choose_strand(strands, sub)
        if strand_heading is None:
            continue

        # Nearest term heading that starts before the strand.
        term_heading = None
        for term in terms:
            if term.index < strand_heading.index:
                if term_heading is None or term.index > term_heading.index:
                    term_heading = term
        if term_heading is None:
            continue

        term = outline.setdefault(term_heading.index, Term(term_heading.text, term_heading.page))
        key = (term_heading.index, strand_heading.text)
        strand = index_of.get(key)
        if strand is None:
            strand = Strand(strand_heading.text, strand_heading.page)
            index_of[key] = strand
            term.strands.append(strand)

        strand.sub_strands.append(SubStrand(sub.text, sub.page))

    # A term with no sub-strands is a table-of-contents entry, not a section.
    return [term for _, term in sorted(outline.items()) if term.strands]


def check_mapping(outline: list[Term]) -> list[str]:
    """Report sub-strands attached to a strand other than the expected one."""
    problems = []
    for term in outline:
        for strand in term.strands:
            for sub_strand in strand.sub_strands:
                expected = EXPECTED_STRAND.get(sub_strand.name)
                if expected and expected != strand.name:
                    problems.append(
                        f"{term.name} p.{sub_strand.page}: {sub_strand.name} "
                        f"attached to {strand.name}, expected {expected}"
                    )
                if expected is None:
                    problems.append(f"unknown sub-strand '{sub_strand.name}' (p.{sub_strand.page})")
    return problems


def load_pages(document: Path, force: bool) -> list[str]:
    """Read the cached text if it is current, otherwise ingest the PDF now."""
    output_path = OUTPUT_DIR / f"{document.name}.txt"

    if force or not output_path.exists() or (
        output_path.stat().st_mtime < document.stat().st_mtime
    ):
        log.info("No current text for %s, extracting now", document.name)
        result = ingest_document(document, force=force)
        if result.status in {"failed", "empty"}:
            raise SystemExit(f"Could not extract {document.name}: {result.reason}")

    text = output_path.read_text(encoding="utf-8")
    return text.split(PAGE_SEPARATOR)


def print_outline(document: Path, pages: list[str], outline: list[Term]) -> None:
    print()
    print("=" * 72)
    print(f"DOCUMENT : {document.name}")
    print(f"PAGES    : {len(pages)}")
    print(f"TERMS    : {len(outline)}")
    print("=" * 72)

    total_sub_strands = 0
    for term in outline:
        print(f"\n{term.name}  (pdf p.{term.page})")
        for strand in term.strands:
            print(f"  {strand.name}  (p.{strand.page})")
            if not strand.sub_strands:
                print("    (no sub-strands detected)")
            for sub_strand in strand.sub_strands:
                total_sub_strands += 1
                print(f"    - {sub_strand.name:<28} p.{sub_strand.page}")

    print()
    print(f"TOTAL sub-strand occurrences: {total_sub_strands}")

    unique = {s.name for t in outline for st in t.strands for s in st.sub_strands}
    print(f"UNIQUE sub-strand names     : {len(unique)}")
    for name in sorted(unique):
        print(f"  * {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List headings in a curriculum PDF.")
    parser.add_argument(
        "--document",
        default=None,
        help="PDF file name inside generator/documents (default: the Teacher's Guide)",
    )
    parser.add_argument("--force", action="store_true", help="re-extract the PDF first")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    documents = get_documents()

    if args.document:
        matches = [p for p in documents if p.name == args.document]
        if not matches:
            raise SystemExit(f"Not in {DOCUMENTS_DIR}: {args.document}")
        document = matches[0]
    else:
        matches = [p for p in documents if "TEACHER" in p.name.upper()]
        if not matches:
            raise SystemExit("No Teacher's Guide found; pass --document explicitly")
        document = matches[0]

    pages = load_pages(document, force=args.force)
    outline = build_outline(pages)

    if not outline:
        print("No TERM headings found. This document does not use the term/strand layout.")
        return 1

    print_outline(document, pages, outline)

    problems = check_mapping(outline)
    print()
    if problems:
        print(f"MAPPING WARNINGS ({len(problems)}):")
        for problem in problems:
            print(f"  ! {problem}")
    else:
        print("MAPPING OK: every sub-strand sits under its expected strand.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
