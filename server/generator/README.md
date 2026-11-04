# generator

Turns the KICD PDFs into clean text, then maps their structure so the RAG layer can
chunk on real headings instead of fixed character counts.

## Files

| File | Role |
|---|---|
| `ingest_documents.py` | Extracts every PDF in `documents/` to `output/<name>.pdf.txt` |
| `probe_structure.py` | Lists terms, strands and sub-strands with PDF page numbers |
| `chunk_curriculum.py` | Splits the Teacher's Guide into lesson chunks (JSONL) |
| `embed_curriculum.py` | Embeds `embedding_text` and upserts to Pinecone |
| `test_retrieval.py` | Runs band-shaped queries and prints top matches |
| `documents/` | Source PDFs |
| `output/` | Extracted text (UTF-8, `\f` between pages) and `teacher_guide_chunks.jsonl` |

> `ingest_curriculum_guide.py` is an earlier draft built around `output.txt` and the
> excluded Grade 2 PDF. It is superseded.

`HI MATHEMATICS GRADE 2.pdf` is excluded: it is a scanned document with no text
layer. The exclusion and its reason live in `EXCLUDED_DOCUMENTS`.

## What `ingest_document()` does

One call handles one file, and it always takes a path returned by `get_documents()`:

1. **Collects file metadata** — name, full path, size in bytes and human units,
   last-modified date, and a streamed SHA-256 (no full-file read into memory).
2. **Skips work that is already done** — if `<name>.pdf.txt` exists and is newer
   than the PDF, it returns `skipped` and extracts nothing. `--force` overrides.
3. **Extracts page by page** — a page that raises is counted and left empty; it
   never aborts the document.
4. **Measures quality** — total characters, pages with under 20 characters, and
   count of U+FFFD replacement characters, so a silent bad extraction is visible.
5. **Writes the text** — UTF-8 without BOM, `\n` newlines, pages joined by a
   form feed (`\f`). Splitting on `\f` recovers page numbers for chunk metadata.
6. **Reports a status** — `ok`, `empty` (no text layer), `skipped` or `failed`
   with the exception name and message.

`get_documents()` is the only place that decides what gets ingested. Drop a PDF in
`documents/` and it is picked up on the next run; the loop in `main()` only does
logging, counting and error isolation.

## Usage

```bash
python generator/ingest_documents.py            # extract, skip current files
python generator/ingest_documents.py --force    # re-extract everything
python generator/probe_structure.py             # map the Teacher's Guide
```

## Log format

```
10:22:53 | INFO    | [2/3] INGESTING  MATHEMATICS_TEACHER GUIDE GRADE 3 24th Dec 2017b.pdf
10:22:53 | INFO    |         path:     ...\generator\documents\MATHEMATICS_TEACHER GUIDE GRADE 3 24th Dec 2017b.pdf
10:22:53 | INFO    |         size:     14.4 MB (15,098,003 bytes)
10:22:53 | INFO    |         modified: 2026-10-21 14:40
10:22:53 | INFO    |         sha256:   0b3ba95bad8aca22...
10:22:53 | INFO    |         pages:    257
10:22:53 | INFO    |         text:     267,283 chars
10:22:53 | INFO    |         quality:  0 empty page(s), 0 bad char(s)
10:22:53 | INFO    |         output:   ...\generator\output\MATHEMATICS_TEACHER GUIDE GRADE 3 24th Dec 2017b.pdf.txt
10:22:53 | INFO    |         status:   OK (3.2s)
```

## Structure of the Teacher's Guide

Three terms, each containing the same three strands and their sub-strands.

```
TERM ONE (p.28)
  NUMBERS (p.29)      NUMBER CONCEPT, WHOLE NUMBERS, FRACTIONS, ADDITION,
                      SUBTRACTION, MULTIPLICATION, DIVISION
  MEASUREMENT (p.70)  LENGTH, MASS, CAPACITY, TIME, MONEY
  GEOMETRY (p.88)     POSITION AND DIRECTION, SHAPES
```

Term Two has no SHAPES section. A strand heading is sometimes extracted at the
*bottom* of the page that starts its first sub-strand, so the probe assigns a
sub-strand to the last strand heading before it, or to a heading later on the
same page.

Body text runs per **lesson** (`Week 1 Lesson 2`, lesson title, specific lesson
learning outcome, resources, activities, `Work to do`). Each term ends with an
`ANSWERS FOR TERM n` section that repeats the same `WEEK n LESSON n` labels, so
those pages must be labelled as answer keys and kept out of the teaching chunks.

## Chunking

`chunk_curriculum.py` produces **one chunk per lesson**, because a lesson is
already one skill: one specific learning outcome, one activity set, one
`Work to do`. Fixed-width splitting would separate the outcome from its
activities.

Each lesson chunk gets the sub-strand preamble prepended (General Learning
Outcome, lesson count, Background Information, cut at a sentence boundary) so it
is self-contained when retrieved.

```bash
python generator/chunk_curriculum.py
```

Output: `generator/output/teacher_guide_chunks.jsonl`, 149 lesson chunks plus
144 answer-key chunks.

| Field | Meaning |
|---|---|
| `chunk_id` | `tg3-one-w01l02-les` = Teacher Guide, term one, week 1 lesson 2 |
| `section` | `lesson` or `answers` |
| `indexable` | `false` for answer keys, so they never ground a quiz |
| `term`, `strand`, `sub_strand` | Curriculum position, copied to answer keys from their lesson |
| `week`, `lesson`, `lesson_title` | Lesson identity |
| `page_start`, `page_end` | PDF pages the chunk came from |
| `text` | Full text for the prompt (lesson body + sub-strand background) |
| `embedding_text` | Under 1,000 chars, since MiniLM truncates near 256 tokens |
| `warnings` | Source problems found while chunking |

Answer pages only repeat `WEEK n LESSON n`, so their strand is taken from the
teaching lesson with the same label. Three source defects are flagged rather than
hidden: Term One has an answer key for `WEEK 11 LESSON 4` but no such lesson, and
two answer labels appear twice.

## Embedding and retrieval

```bash
python generator/embed_curriculum.py --dry-run   # 3 chunks, no network calls
python generator/embed_curriculum.py             # upsert 149 lesson chunks
python generator/test_retrieval.py               # 6 band-shaped queries
```

Index `cbc-curriculum-rag`: 384 dimensions, cosine, AWS `us-east-1` serverless.
The script embeds `embedding_text`, stores `text` in metadata for the prompt, and
skips answer keys. `--reset` clears stale vectors; `--recreate` rebuilds the index
if its dimension is wrong.
