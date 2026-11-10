# Chunking the Grade 3 Teacher's Guide

This document describes the corpus artifact at
`generator/output/teacher_guide_chunks.jsonl`: what produced it, what each field means,
what it contains, and what is still missing.

**Status:** the output is a checked-in artifact. The script that produced it is not in the
working tree or in this repository's reachable history. Do not assume the commands below
can regenerate it today; see [Provenance](#provenance).

---

## 1. Source

| Item | Value |
|---|---|
| Document | `generator/documents/MATHEMATICS_TEACHER GUIDE GRADE 3 24th Dec 2017b.pdf` |
| Pages | 257 |
| Extracted text | 267,283 characters |
| Terms | 3 |
| Strands | 3 — NUMBERS, MEASUREMENT, GEOMETRY |
| Sub-strands | 14 |

Extraction is handled by `generator/ingest_documents.py`. It writes UTF-8 text with pages
joined by a form feed (`\f`), so page numbers can be recovered later. Structure (terms,
strands, sub-strands) is mapped by `generator/probe_structure.py`.

Grade 2 is excluded from the corpus: `HI MATHEMATICS GRADE 2.pdf` is a scan with no text
layer.

---

## 2. Segmentation rule

The corpus is **one chunk per lesson**, not fixed-width splitting. A lesson already
contains one skill: one specific learning outcome, one activity set, one `Work to do`.
Fixed-width splitting would separate the outcome from its activities.

- **149 lesson chunks** (`section="lesson"`, `indexable=true`).
- **144 answer-key chunks** (`section="answers"`, `indexable=false`).
- Each lesson chunk prepends its sub-strand preamble (General Learning Outcome, lesson
  count, Background Information, cut at a sentence boundary) so it is self-contained when
  retrieved.
- Answer keys repeat `WEEK n LESSON n` labels, so their strand is copied from the teaching
  lesson with the same label. They are never embedded or used to ground a quiz.

### `text` vs `embedding_text`

| Field | Content | Length |
|---|---|---|
| `text` | Full lesson body plus sub-strand preamble. Used in the generation prompt. | 1,326–2,117 chars (median 1,752) |
| `embedding_text` | Normalised context header (`Term One \| Numbers \| Number Concept \| Week 1 Lesson 1: <title>`) followed by the lesson body, truncated below 1,000 characters at a sentence boundary. | 614–998 chars; all 149 end with `.` |

MiniLM truncates near 256 tokens, so embedding the full `text` would drop the learning
activities. The full text is retained in metadata for the prompt.

---

## 3. Chunk schema

Each line of the JSONL is one chunk.

| Field | Type | Meaning |
|---|---|---|
| `chunk_id` | string | Stable ID, e.g. `tg3-one-w01l02-les` = Teacher Guide, term one, week 1, lesson 2, lesson. Answer keys end in `-ans`; duplicate answer labels end in `-ans-2`. |
| `section` | `lesson` \| `answers` | Teaching chunk or answer-key chunk. |
| `indexable` | bool | `false` for answer keys, so they never ground a quiz. |
| `document` | string | Source PDF filename. |
| `term` | string | `TERM ONE`, `TERM TWO`, `TERM THREE`. |
| `strand` | string | `NUMBERS`, `MEASUREMENT`, `GEOMETRY`. |
| `sub_strand` | string | One of 14 sub-strands (e.g. `ADDITION`, `MONEY`). |
| `week` | int | Week number from the lesson label. |
| `lesson` | int | Lesson number within the week. |
| `lesson_title` | string | Title from the guide, e.g. `Ordinal Number Names (first to fifth)`. |
| `has_outcome` | bool | Source contains a Specific Lesson Learning Outcome. |
| `has_activities` | bool | Source contains a Learning Activities section. |
| `page_start` | int | First PDF page of the chunk. |
| `page_end` | int | Last PDF page of the chunk. |
| `char_count` | int | Length of `text`. |
| `text` | string | Full content for the prompt. |
| `embedding_text` | string | Truncated, header-prefixed text that is embedded. |
| `warnings` | list[string] | Source defects found while chunking. Empty for 290 of 293 chunks. |

---

## 4. Corpus statistics

### Totals

| Section | Chunks |
|---|---|
| Lesson (`indexable=true`) | 149 |
| Answer key (`indexable=false`) | 144 |
| **Total** | **293** |

All 293 `chunk_id` values are unique.

### Lesson chunks by term and strand

| Term | NUMBERS | MEASUREMENT | GEOMETRY | Total |
|---|---|---|---|---|
| TERM ONE | 37 | 14 | 3 | 54 |
| TERM TWO | 38 | 15 | 2 | 55 |
| TERM THREE | 27 | 11 | 2 | 40 |
| **Total** | **102** | **40** | **7** | **149** |

### Lesson chunks by sub-strand

| Strand | Sub-strand | Lessons |
|---|---|---|
| NUMBERS | ADDITION | 25 |
| NUMBERS | WHOLE NUMBERS | 21 |
| NUMBERS | SUBTRACTION | 20 |
| NUMBERS | FRACTIONS | 10 |
| NUMBERS | MULTIPLICATION | 10 |
| NUMBERS | NUMBER CONCEPT | 8 |
| NUMBERS | DIVISION | 8 |
| MEASUREMENT | MONEY | 10 |
| MEASUREMENT | TIME | 10 |
| MEASUREMENT | CAPACITY | 8 |
| MEASUREMENT | LENGTH | 6 |
| MEASUREMENT | MASS | 6 |
| GEOMETRY | POSITION AND DIRECTION | 5 |
| GEOMETRY | SHAPES | 2 |
| **Total** | | **149** |

### Quality checks on lesson chunks

- No lesson is missing `has_outcome` or `has_activities`.
- `text` length: 1,326–2,117 chars.
- `embedding_text` length: 614–998 chars; no empty values; none exceeds 1,000.
- Weeks present: 1–11.
- Label duplicates within lesson chunks: none.

---

## 5. Known source defects

These are recorded in `warnings` rather than hidden or silently corrected.

| Chunk | Warning | Meaning |
|---|---|---|
| `tg3-one-w10l04-ans-2` | `duplicate lesson label in source` | The guide repeats a `WEEK 10 LESSON 4` answer label. |
| `tg3-three-w08l04-ans-2` | `duplicate lesson label in source` | The guide repeats a `WEEK 8 LESSON 4` answer label. |
| `tg3-one-w11l04-ans` | `no matching lesson for this answer key` | Term One has an answer key for `WEEK 11 LESSON 4` but no such teaching lesson. |

Other limitations:

- **15 answer chunks are under 40 characters**, e.g. `WEEK 3 LESSON 4` with no answers, or
  `NB: Reading lesson`. They carry no retrievable content. They are not embedded.
- **Term Two has no `SHAPES` section.** Geometry in Term Two is only `POSITION AND
  DIRECTION`.
- **Geometry is thin:** 7 lesson chunks against 102 for Numbers. Retrieval for Geometry
  must use a sub-strand filter, or arithmetic will dominate.
- **Layout is lost:** stacked fractions, vertical addition and diagrams survive only as
  linearised text or images.
- **Cross-references dangle:** the guide points at learner's book pages and digital games
  that are not in the corpus.

---

## 6. Provenance

| Item | Value |
|---|---|
| Path | `generator/output/teacher_guide_chunks.jsonl` |
| Size | 572,534 bytes |
| Lines | 293 |
| SHA-256 | `A46048E75B126CB8D2C6E165BD8239E81D54A2F31CE3B7B149B3C22CA5B009FD` |
| Added to repo | commit `5600a7e`, 2026-11-04 |

The chunker (`generator/chunk_curriculum.py`) referenced by `README.md` and `REPORT.md` is
**not present in the working tree and not recoverable from reachable history**. The only
`chunk_curriculum.py` in git history is an earlier, superseded draft that used a
fixed-width `RecursiveCharacterTextSplitter` over `output.txt`; it did not produce this
JSONL and must not be used to regenerate it.

Consequences:

- The JSONL is the authoritative artifact.
- The reproduction commands in `README.md` and `REPORT.md` cannot be run as written.
- To regenerate the corpus, the lesson-boundary chunker would have to be reconstructed
  from the documented rules and its output diffed against the tracked JSONL.

---

## 7. Handoff to embedding

`generator/embed_curriculum.py` reads this file and embeds only chunks with
`indexable=true`:

- Model: `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, cosine.
- Input: `embedding_text`.
- Stored in Pinecone metadata: `text`, `term`, `strand`, `sub_strand`, `week`, `lesson`,
  `lesson_title`, `section`, `indexable`, `page_start`, `page_end`, `char_count`.
- Answer keys (`section="answers"`) are skipped.
- Embedded: **149 vectors** on 2026-11-09. Run details:
  `generator/output/embedding_manifest.json`.
