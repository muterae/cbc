# Presentation Notes — The Curriculum Layer (Generator)

Simple explanations, the numbers to quote, and an honest list of what is still missing.

---

## 0. The 30-second version

> The predictor decides **how hard** a quiz should be. This layer decides **what to
> teach**. We took the official KICD Grade 3 Mathematics Teacher's Guide, cleaned 257
> pages of text, mapped its 3 terms and 14 sub-strands, and cut it into 293 chunks:
> 149 complete lessons plus 144 answer keys. The lessons are ready to embed. Embedding
> and retrieval are the next step.

---

## 1. Why this layer exists

The classifier outputs a band: Below, Approaching, Meeting or Exceeding. That is a
difficulty, not a lesson. Something has to fetch the actual curriculum content.

Without retrieval, the language model invents questions. They look plausible and teach
nothing in particular. With retrieval, every question can be traced back to a page of the
Teacher's Guide.

Think of it as an **open-book exam**:

- the model writes the question,
- the book is the KICD curriculum,
- the model is only allowed to use the pages it was given.

The layer has three jobs:

1. **Retrieve** the lesson that matches the strand and sub-strand.
2. **Ground** the prompt in that lesson's outcome, activities and resources.
3. **Constrain** the output to the rules for the predicted band.

Only job 1's raw material exists so far: the corpus.

---

## 2. The corpus

| Document | Pages | Extracted chars | Verdict |
|---|---:|---:|---|
| Teacher's Guide, Grade 3 | 257 | 267,283 | **Primary corpus** |
| Pupils Book, Grade 3 | 261 | 119,542 | Sparse — mostly images |
| CBA framework | 5 | 9,125 | Usable, **not chunked yet** |
| Grade 2 Mathematics | 48 | 0 | **Excluded — pure scan** |

**Why Grade 3, not Grade 2?** The only Grade 2 document is a scan with no text layer.
Extracting it would need OCR of all 48 pages, and the result would cover a different
grade from the rest. The project scope was therefore restated as Grade 3 Mathematics.

The Pupils Book averages 458 characters per page, so its content is pictures, not
sentences. It cannot supply exercises without OCR.

---

## 3. What was built

```
PDF  →  clean text  →  structure map  →  lesson chunks  →  [ embeddings ]
       ingest_documents   probe_structure   chunker          INCOMPLETE
```

### 3.1 Extraction — done

`ingest_documents.py` extracts page by page with `pypdf` and joins pages with a form feed
(`\f`), so page numbers survive into chunk metadata.

It also does the boring things that make a corpus trustworthy:

- records name, size, modification date and SHA-256 for every source;
- skips a file if its text is newer than the PDF (`--force` overrides);
- survives a bad page instead of aborting the document;
- measures text quality: characters, empty pages, replacement characters, mojibake.

**The bug worth mentioning.** The previous extraction reused one output file handle, so
four ``.txt`` files ended up byte-identical — every one contained the Teacher's Guide
title page, whatever its name claimed. The fix was one handle per document, fixed UTF-8,
and the metadata above.

| Check | Teacher's Guide |
|---|---:|
| Pages | 257 |
| Characters | 267,283 |
| Mean characters per page | 1,040 |
| Empty pages (<20 chars) | 0 |
| Replacement characters | 0 |
| Mojibake sequences | 0 |

Fractions survive as real characters: `½` ×15 and `¼` ×16. That matters for a maths
corpus.

### 3.2 Structure map — done

The guide has three terms, each repeating the same three strands:

| Term | Starts | NUMBERS | MEASUREMENT | GEOMETRY |
|---|---:|---:|---:|---:|
| Term One | p.28 | p.29 | p.70 | p.88 |
| Term Two | p.114 | p.115 | p.158 | p.175 |
| Term Three | p.192 | p.193 | p.226 | p.241 |

Fourteen unique sub-strands, appearing 41 times (14 × 3, minus SHAPES in Term Two).

**A layout trap.** The strand heading is sometimes extracted at the *bottom* of the page
that starts its first sub-strand. On p.70 the order is `LENGTH` → background →
`MEASUREMENT`, so naive reading assigns Length (a Measurement topic) to Numbers. The
probe assigns each sub-strand to the last strand heading before it, unless a strand
heading appears later on the same page.

Validation: **41 of 41** sub-strand occurrences land under the expected strand.

**The unit is a lesson.** Body pages follow a fixed pattern — Week n Lesson n, title,
specific learning outcome, resources, key inquiry question, activities, `Work to do`.
One lesson is one skill. That is the natural unit for grounding a quiz.

### 3.3 Lesson chunking — done

**Decision: one chunk per lesson**, with its sub-strand preamble attached.

| Rejected option | Why |
|---|---|
| Fixed 700–800 character windows | Cuts the outcome away from the activities that teach it |
| One chunk per sub-strand | 5–25 lessons per chunk; too broad to ground one quiz |
| Two indexes (lesson + sub-strand) | Doubles embedding work for little gain at 149 lessons |

Each lesson chunk carries:

- the lesson body: marker, title, outcome, resources, key inquiry question, activities,
  `Work to do`;
- the sub-strand preamble: General Learning Outcome, lesson count, Background
  Information, capped and cut at a sentence boundary.

Two details that matter later:

- **`embedding_text` is under 1,000 characters.** MiniLM truncates near 256 tokens; the
  full 2,000-character chunk would silently lose the activities. The full `text` is kept
  for the prompt.
- **Answer keys are `indexable=false`.** They repeat `WEEK n LESSON n` but contain only
  answers, so they must never ground a generated quiz. There are 144 of them.

Output: `generator/output/teacher_guide_chunks.jsonl`, 293 lines.

---

## 4. What the numbers say

| Metric | Value |
|---|---:|
| Total chunks | 293 |
| Lesson chunks (indexable) | 149 |
| Answer-key chunks (not indexable) | 144 |
| Lessons in Term One / Two / Three | 54 / 55 / 40 |
| Lessons by strand: Numbers / Measurement / Geometry | 102 / 40 / 7 |
| Lesson chunk characters, minimum | 1,326 |
| Lesson chunk characters, median | 1,752 |
| Lesson chunk characters, maximum | 2,117 |
| Embedding text characters | 614 – 998 |
| PDF pages covered by lessons | 29 – 244 |

The imbalance is the story: **102 Number lessons against 7 Geometry lessons**. A
whole-index search will be dominated by arithmetic. Retrieval will need a sub-strand
filter, not just similarity.

### 4.1 Sub-strand breakdown

| Strand | Sub-strand | Lessons |
|---|---|---:|
| Numbers | Number Concept | 8 |
| Numbers | Whole Numbers | 21 |
| Numbers | Fractions | 10 |
| Numbers | Addition | 25 |
| Numbers | Subtraction | 20 |
| Numbers | Multiplication | 10 |
| Numbers | Division | 8 |
| Measurement | Length | 6 |
| Measurement | Mass | 6 |
| Measurement | Capacity | 8 |
| Measurement | Time | 10 |
| Measurement | Money | 10 |
| Geometry | Position and Direction | 5 |
| Geometry | Shapes | 2 |

### 4.2 Validation

| Check | Result |
|---|---|
| Sub-strands attached to the expected strand | 41 / 41 |
| Lessons with a title, outcome and activities | 149 / 149 |
| Answer keys matched to a teaching lesson | 144 / 144 |
| Stray headers, folios or duplicate labels left in text | 0 |
| Empty lesson chunks | 0 |

### 4.3 Defects in the source — recorded, not hidden

1. **Orphan answer key.** Term One has answers for `WEEK 11 LESSON 4`, but the guide has
   no such lesson; the sequence jumps from W11 L3 to W11 L5.
2. **Duplicate answer labels.** `WEEK 10 LESSON 4` (Term One) and `WEEK 8 LESSON 4`
   (Term Three) each appear twice.
3. **Missing sub-strand.** Term Two has no SHAPES section.
4. **Empty answer keys.** 15 answer chunks are under 40 characters and carry nothing
   retrievable.

Each defect is written into the `warnings` field of the affected chunk, so it surfaces in
the data instead of disappearing.

---

## 5. Questions you will probably get

| Question | Short answer |
|---|---|
| What is RAG? | An open-book exam: fetch the right pages first, then let the model write only from them |
| Why not fixed 700-character chunks? | They split the learning outcome from the activities that teach it |
| Why one chunk per lesson? | A lesson is already one skill: one outcome, one activity set, one `Work to do` |
| Why is the embedding text shorter than the chunk? | MiniLM cuts off near 256 tokens; the short field keeps the outcome and activities |
| Will answer keys leak into quizzes? | No — they are marked `indexable=false` and skipped when embedding |
| How do you know the structure is right? | 41/41 sub-strands, 149/149 complete lessons, 144/144 matched answer keys |
| Why Grade 3 and not Grade 2? | The Grade 2 PDF is a scan: 48 pages, 0 characters |
| Is the content official? | It is the KICD Grade 3 Mathematics Teacher's Guide |
| Why is Geometry weak? | Only 7 lessons exist; retrieval must filter by sub-strand or arithmetic will dominate |
| What happens to diagrams? | They are images or linearised text; number glyphs survive, layout does not |
| What if retrieval fails? | A static fallback of core benchmarks is planned (not built yet) |

---

## 6. Numbers to memorise

- 257 pages, 267,283 characters
- 3 terms, 3 strands, **14 sub-strands**, 41 occurrences
- **293 chunks = 149 lessons + 144 answer keys**
- 149 = 54 + 55 + 40 across the terms
- 102 / 40 / 7 lessons by strand
- 1,752 characters — median lesson chunk
- 614–998 characters — embedding text
- 41/41, 149/149, 144/144 — the three validation checks
- Grade 2: 48 pages, 0 characters

---

## 7. INCOMPLETE — remaining work

Nothing below has been run. The scripts exist; the outputs do not.

| Stage | Status |
|---|---|
| PDF extraction | done |
| Structure map | done |
| Lesson chunking | done (JSONL output) |
| Embedding to vector store | **INCOMPLETE** |
| Retrieval smoke test | **INCOMPLETE** |
| CBA framework chunking | **INCOMPLETE** |
| Band playbook + few-shots | **INCOMPLETE** |
| Quiz synthesis service | **INCOMPLETE** |
| API integration | **INCOMPLETE** |
| Evaluation | **INCOMPLETE** |

**1. Embeddings — INCOMPLETE.** `embed_curriculum.py` is written but has never run.
`torch`, `sentence-transformers` and `pinecone` are not installed, so there are currently
**0 vectors**. The plan: MiniLM, 384 dimensions, cosine, Pinecone serverless in
`us-east-1`, index `cbc-curriculum-rag`, 149 lesson chunks only.

**2. Retrieval test — INCOMPLETE.** `test_retrieval.py` defines six band-shaped queries
(ordinal numbers, two-digit addition, quarters, missing-number subtraction, change,
turning left and right). None has been run. There is no precision@k, no evidence yet that
top-3 returns the right lesson.

**3. CBA framework — INCOMPLETE.** The 5-page assessment document is extracted but not
chunked. Until it is, the BE/AE/ME/EE descriptions in the playbook have no grounded
source.

**4. Playbook — INCOMPLETE.** No `mathematics.grade3.yaml`, no few-shot file, no loader.
The lever sets and band rules are designed but not written.

**5. Quiz synthesis — INCOMPLETE.** No prompt assembly, no Groq call, no JSON validation,
no deterministic fallback. The contract exists only on paper.

**6. API — INCOMPLETE.** `/api/v1/adaptive-quiz` is still a stub. The band is not yet
connected to retrieval or generation.

**7. Evaluation — INCOMPLETE.** No retrieval quality measurement, no answer-correctness
check, no teacher review of generated questions.

**8. Corpus gaps — INCOMPLETE.** Pupils Book needs OCR; diagrams and stacked fractions
are lost in text; Geometry is thin; cross-references to learner's book pages dangle.

**9. Reproducibility — INCOMPLETE.** The lesson-chunking script is not currently in the
working tree; only `teacher_guide_chunks.jsonl` is present. The corpus cannot be rebuilt
from a clean checkout until that script is restored and committed.

### What to say when you reach this slide

> "The corpus is finished and validated. The next step is embedding the 149 lessons and
> proving retrieval works before any generation code depends on it. I am not going to
> claim the RAG layer works until I can show the query results."
