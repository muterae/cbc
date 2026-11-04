# Corpus Report — Grade 3 Mathematics RAG Layer

Date: 2026-10-22
Scope: extraction, structure analysis and chunking of the KICD documents in
`generator/documents/`. This covers the retrieval corpus only; the predictor is
documented in `predictor/REPORT.md`.

---

## 1. Corpus

| Document | Pages | Size | Extracted chars | Verdict |
|---|---:|---:|---:|---|
| `MATHEMATICS_TEACHER GUIDE GRADE 3 24th Dec 2017b.pdf` | 257 | 14.4 MB | 267,283 | **Primary corpus** |
| `MATHEMATICS_PUPILS BOOK_ GRADE  3 22nd Dec.pdf` | 261 | 46.9 MB | 119,542 | Usable but sparse |
| `UNDERSTANDING-THE-COMPETENCY-BASED-ASSESSMENT-CBA-pdf.pdf` | 5 | 696 KB | 9,125 | Usable, not yet chunked |
| `HI MATHEMATICS GRADE 2.pdf` | 48 | 12.7 MB | 0 | **Excluded** — scanned images |

The corpus is Grade 3, not Grade 2. Only `HI MATHEMATICS GRADE 2.pdf` covers
Grade 2 and it has no text layer, so the project scope is restated as **Grade 3
Mathematics**.

---

## 2. Extraction audit

### 2.1 The previous extraction was wrong

Five `.txt` files existed in `generator/output/`, but four were byte-identical:

| Property | Value |
|---|---|
| SHA-256 | `5E2AAFAD4E77A35B6A2F32FEFA78D00FAE37FF37E70950217EDA942E086C4602` |
| Size | 275,630 bytes each |
| Content | Teacher's Guide title page, not the file the name claimed |

Affected names: `HI MATHEMATICS GRADE 2.pdf.txt`, `MATHEMATICS_PUPILS BOOK...txt`,
`MATHEMATICS_TEACHER GUIDE...txt`, `UNDERSTANDING-THE-CBA...txt`.

The fifth file, `HI MATHEMATICS GRADE 2.txt` (64,121 bytes), was a separate OCR
of page 1 only. Root cause: the extraction loop reused one output handle, so the
last document written overwrote every earlier name with its own text. The writer
also lacked a fixed encoding, which produced mojibake such as `Teachers�?T`.

### 2.2 Why Grade 2 is excluded

`HI MATHEMATICS GRADE 2.pdf` returns **0 characters across 48 pages**. It is a
pure scan. Extracting it needs OCR of every page, and the result would cover a
different grade from the rest of the corpus. It is therefore excluded by name in
`EXCLUDED_DOCUMENTS`, with the reason recorded in code rather than in a comment.

### 2.3 Current extraction

`ingest_documents.py` uses `pypdf`, extracts page by page, and joins pages with a
form feed (`\f`) so page numbers survive into chunk metadata. Output is UTF-8
without BOM and `\n` newlines.

| Check | Teacher Guide | Pupils Book | CBA |
|---|---:|---:|---:|
| Pages | 257 | 261 | 5 |
| Empty pages (<20 chars) | 0 | 1 | 0 |
| U+FFFD replacement chars | 0 | 0 | 0 |
| Mojibake sequences (`â€`, `Ã`) | 0 | 0 | 0 |
| Mean chars per page | 1,040 | 458 | 1,825 |

Non-ASCII characters in the Teacher's Guide are legitimate glyphs, not damage:
U+2019 curly apostrophe ×370, U+2022 bullet ×52, U+201C/U+201D quotes ×22 each,
U+00BC ¼ ×16, U+00BD ½ ×15. Fractions survive as real characters.

The Pupils Book's 458 chars per page mean most of its content is images. Only 8 of
257 pages exceed 800 characters, so its text alone cannot supply exercises.

Source hashes of the accepted files:

| File | SHA-256 (first 16) |
|---|---|
| Teacher's Guide | `0b3ba95bad8aca22` |
| Pupils Book | `6242d03b8f296fa4` |
| CBA | `86eba150acb83403` |

---

## 3. Structure of the Teacher's Guide

Three terms, each repeating the same three strands:

| Term | Starts | NUMBERS | MEASUREMENT | GEOMETRY |
|---|---:|---:|---:|---:|
| TERM ONE | p.28 | p.29 | p.70 | p.88 |
| TERM TWO | p.114 | p.115 | p.158 | p.175 |
| TERM THREE | p.192 | p.193 | p.226 | p.241 |

41 sub-strand occurrences, 14 unique sub-strands:

| Strand | Sub-strand | Lessons |
|---|---|---:|
| NUMBERS | NUMBER CONCEPT | 8 |
| NUMBERS | WHOLE NUMBERS | 21 |
| NUMBERS | FRACTIONS | 10 |
| NUMBERS | ADDITION | 25 |
| NUMBERS | SUBTRACTION | 20 |
| NUMBERS | MULTIPLICATION | 10 |
| NUMBERS | DIVISION | 8 |
| MEASUREMENT | LENGTH | 6 |
| MEASUREMENT | MASS | 6 |
| MEASUREMENT | CAPACITY | 8 |
| MEASUREMENT | TIME | 10 |
| MEASUREMENT | MONEY | 10 |
| GEOMETRY | POSITION AND DIRECTION | 5 |
| GEOMETRY | SHAPES | 2 |

### 3.1 Layout quirk

The strand heading is sometimes extracted at the **top** of a page and sometimes
at the **bottom**, even when the sub-strand heading is at the top. On p.70 the
order is `LENGTH` heading → background → `MEASUREMENT`. Reading the text
sequentially therefore assigns `LENGTH` (a Measurement sub-strand) to Numbers.

The probe handles this by assigning each sub-strand to the last strand heading
before it, unless a strand heading appears later on the same page, in which case
that one wins. Validation: 41 of 41 sub-strand occurrences land under the
expected strand.

### 3.2 The teaching unit is a lesson

Body pages follow a fixed pattern:

```
Week 1 Lesson 1
NUMBER CONCEPT
Ordinal Number Names (first to fifth)
Specific Lesson Learning Outcome
Learning Resources
Key Inquiry Question
Learning Activities
Work to do
```

A lesson is one skill with one observable outcome and one activity set — the
natural unit for quiz grounding. Fixed-width splitting separates the outcome from
the activities that teach it, which makes a retrieved chunk unusable as a prompt.

Each term ends with `ANSWERS FOR TERM n`, which repeats `WEEK n LESSON n` labels
but contains only answers.

---

## 4. Chunking design

**Decision:** one chunk per lesson, with its sub-strand preamble attached.

Rejected alternatives:

| Option | Why not |
|---|---|
| Fixed 700–800 char windows | Cuts outcome from activities; breaks tables and numbered activity lists |
| One chunk per sub-strand | 5–25 lessons per chunk; too broad to ground a single quiz |
| Two indexes (lesson + sub-strand) | Better recall, but unnecessary at 149 lessons and doubles the embedding work |

Chunk contents:

- Lesson body: marker, sub-strand label, title, outcome, resources, key inquiry
  question, activities, `Work to do`.
- Sub-strand preamble prepended: General Learning Outcome, lesson count, and
  Background Information, capped at 900 chars and cut at a sentence boundary.
- `embedding_text`: header (`Term One | Numbers | Number Concept | Week 1 Lesson 1`)
  plus the body from the outcome onward, capped under 1,000 chars. The full 2,000
  char chunk is not embedded because MiniLM truncates near 256 tokens, which would
  silently drop the activities.
- Answer keys: emitted with `section="answers"` and `indexable=false`. Answer
  pages carry no strand information of their own, so strand, sub-strand and title
  are copied from the teaching lesson with the same `(term, week, lesson)` label.

---

## 5. Chunk statistics

| Metric | Value |
|---|---:|
| Total chunks | 293 |
| Lesson chunks | 149 |
| Answer-key chunks | 144 |
| Lessons in Term One / Two / Three | 54 / 55 / 40 |
| Lessons by strand (Numbers / Measurement / Geometry) | 102 / 40 / 7 |
| Lesson chunk chars, min | 1,326 |
| Lesson chunk chars, median | 1,752 |
| Lesson chunk chars, p90 | 1,991 |
| Lesson chunk chars, max | 2,117 |
| Embedding text chars | 614 – 998 |
| Answer chunk chars, median | 86.5 |
| Answer chunk chars, max | 455 |
| PDF pages covered by lessons | 29 – 244 |

Output: `generator/output/teacher_guide_chunks.jsonl` (293 lines, one JSON object
per chunk).

---

## 6. Validation

| Check | Result |
|---|---|
| Sub-strands attached to the expected strand | 41 / 41 |
| Lessons with a title, outcome and activities | 149 / 149 |
| Answer keys matched to a teaching lesson | 144 / 144 |
| Running headers / folios / stray strand labels left in text | 0 |
| Empty lesson chunks | 0 |

---

## 7. Defects in the source

These are recorded in the `warnings` field of the affected chunks, not hidden:

1. **Orphan answer key.** Term One has an answer key for `WEEK 11 LESSON 4`, but
   the guide contains no such lesson. The teaching sequence jumps from W11 L3 to
   W11 L5.
2. **Duplicate answer labels.** `WEEK 10 LESSON 4` (Term One) and `WEEK 8 LESSON 4`
   (Term Three) each appear twice in the answer sections.
3. **Missing sub-strand.** Term Two has no `SHAPES` section; Geometry in Term Two
   is only `POSITION AND DIRECTION`.
4. **Empty answer keys.** 15 answer chunks are under 40 characters, e.g.
   `WEEK 3 LESSON 4` with no answers, or `NB: Reading lesson`. They carry no
   retrievable content.

---

## 8. Limitations and risks

1. **Geometry is thin.** 7 lesson chunks against 102 for Numbers. A quiz request
   for Geometry will have little to retrieve, and embedding search across the
   whole index will be dominated by arithmetic.
2. **Pupils Book is not usable as text.** 458 chars per page, mostly images. Its
   value — exercise and question style, and the page numbers the Teacher's Guide
   refers to (`learner's book page 23`) — needs OCR before it can be indexed.
3. **CBA is not chunked.** The BE/AE/ME/EE wording used in prompts must come from
   this document; until it is chunked, the band playbook has no grounded source.
4. **Layout loss.** Stacked fractions, vertical addition and diagrams are images
   or linearised text. Number glyphs survive, spatial relationships do not.
5. **Cross-references dangle.** The guide points at learner's book pages and
   digital games that are not in the corpus.
6. **Chunk overlap is zero by design.** Retrieval must fetch 3 chunks where one
   chunk is not enough; the sub-strand preamble compensates by repeating context
   inside each lesson chunk.

---

## 9. Next steps

1. Chunk the CBA framework by section (5 pages, roughly one chunk per competency
   level) and tag each chunk with the band it describes.
2. Embed `embedding_text` with `all-MiniLM-L6-v2` (384 dimensions, cosine) and
   upsert to a Pinecone serverless index, storing `text` in metadata for the
   prompt. Do not index `section="answers"` chunks.
3. Metadata filters for retrieval: `grade=3`, `subject=mathematics`, `term`,
   `strand`, `sub_strand`, `week`, `lesson`, `section`, `indexable`.
4. Build the retriever with Top-K (default 3), band-aware query construction, and
   the static fallback required by the guardrails.

---

## 10. Reproducing this report

```bash
python generator/ingest_documents.py --force   # extract all PDFs
python generator/probe_structure.py            # verify the outline
python generator/chunk_curriculum.py           # write 293 chunks
```
