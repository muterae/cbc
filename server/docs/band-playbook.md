# CBC band playbook

> Generated from `services/band_playbook.py`. Do not edit by hand.
> Regenerate with `python -m services.band_playbook`.

This table defines the difficulty ceiling for each CBC competency band.
The retrieved KICD lesson supplies the skill; the band supplies the level.

## Difficulty ladder

| Band | Code | Rank | Questions | Numbers | Regrouping | Max steps | Max words |
|---|---|---|---|---|---|---|---|
| Below Expectation | BE | 1 | 4 | 0-10 | No | 1 | 12 |
| Approaching Expectation | AE | 2 | 5 | 0-20 | No | 1 | 20 |
| Meeting Expectation | ME | 3 | 5 | 0-100 | Yes | 2 | 30 |
| Exceeding Expectation | EE | 4 | 6 | 0-100 | Yes | 3 | 40 |

## Below Expectation (BE)

Learner needs concrete support to recognise numbers and complete one-step counting tasks.

| Property | Value |
|---|---|
| Cognitive level | Recognise and count with concrete support |
| Task style | Direct counting or matching with objects, pictures or counters. |
| Context | Classroom counters, sticks, bottle tops and learners. |
| Hint style | Step-by-step physical action, e.g. touch each object while counting. |
| Distractor policy | Options visibly different in size; avoid near-misses. |
| Teacher insight | Learner is practising counting and number recognition with concrete support. |

### Prompt directives

- Use numbers from 0 to 10 only.
- Use concrete objects or pictures described in words.
- Ask one direct question with one action.
- Keep the question at or under 12 words.
- Make the correct option clearly different from the distractors.
- Give a hint that tells the learner exactly what to do physically.

### Forbidden

- No carrying or borrowing (regrouping).
- No multi-step word problems.
- No missing-number or inverse reasoning.
- No abstract symbols without a concrete context.
- No negative numbers.

### Example item

**Question:** There are 4 mangoes. How many mangoes are there?

- A) 2
- B) 3
- C) 4
- D) 5

**Correct answer:** C) 4

**Hint:** Touch each mango as you count: one, two, three, four.

## Approaching Expectation (AE)

Learner can apply a single familiar procedure with numbers up to 20 when the context is familiar.

| Property | Value |
|---|---|
| Cognitive level | Apply one familiar procedure |
| Task style | One-step arithmetic or a short word problem with familiar realia. |
| Context | Kenyan everyday objects: mangoes, shillings, sukuma wiki, pencils. |
| Hint style | Rule reminder, e.g. count on from the larger number. |
| Distractor policy | One off-by-one near-miss; the other options are clearly wrong. |
| Teacher insight | Learner is applying single-step arithmetic in familiar everyday contexts. |

### Prompt directives

- Use numbers from 0 to 20 only.
- Use one operation and one step.
- Use familiar Kenyan objects or money.
- Do not require carrying or borrowing.
- Keep the question at or under 20 words.
- Include one near-miss distractor.

### Forbidden

- No carrying or borrowing (regrouping).
- No multi-step word problems.
- No missing-number or inverse reasoning.
- No negative numbers.
- No unfamiliar or abstract contexts.

### Example item

**Question:** Amina has 12 mangoes. She buys 5 more. How many mangoes does she have now?

- A) 15
- B) 16
- C) 17
- D) 18

**Correct answer:** C) 17

**Hint:** Start at 12 and count 5 steps forward.

## Meeting Expectation (ME)

Learner can apply Grade 3 KICD skills to standard one- and two-step tasks.

| Property | Value |
|---|---|
| Cognitive level | Apply standard Grade 3 procedures |
| Task style | KICD end-of-sub-strand tasks; one- and two-step word problems. |
| Context | Familiar school and home contexts with Kenyan realia. |
| Hint style | Self-checking prompt, e.g. identify the operation and estimate the answer. |
| Distractor policy | Include a common misconception distractor, e.g. wrong operation or off-by-one. |
| Teacher insight | Learner is applying Grade 3 skills to standard one- and two-step tasks. |

### Prompt directives

- Use numbers from 0 to 100.
- Allow carrying and borrowing.
- Use one or two steps.
- Use a KICD-style word problem.
- Keep the question at or under 30 words.
- Include a distractor based on a common misconception.
- Hint should help the learner check the operation or estimate the answer.

### Forbidden

- No inverse or missing-number reasoning.
- No more than two steps.
- No negative numbers.
- No ambiguous wording.
- No content beyond the Grade 3 KICD sub-strand.

### Example item

**Question:** A pencil costs 5 shillings. How much do 4 pencils cost?

- A) 9
- B) 15
- C) 20
- D) 25

**Correct answer:** C) 20

**Hint:** Multiply the cost of one pencil by the number of pencils. Check by adding 5 four times.

## Exceeding Expectation (EE)

Learner can reason with inverse relationships, missing operators and multi-step problems.

| Property | Value |
|---|---|
| Cognitive level | Analyse, reason and transfer |
| Task style | Inverse reasoning, missing-number or missing-operator problems, comparison and multi-step tasks. |
| Context | Less familiar or novel contexts that require transfer. |
| Hint style | Strategy nudge, e.g. work backwards or test each option. |
| Distractor policy | Include a near-miss based on the inverse error; all options plausible. |
| Teacher insight | Learner is reasoning with inverse and multi-step problems and explaining their thinking. |

### Prompt directives

- Use numbers from 0 to 100.
- Allow carrying and borrowing.
- Include inverse reasoning, a missing number or operator, or a multi-step problem.
- Use a less familiar context to test transfer.
- Keep the question at or under 40 words.
- Include plausible distractors that reflect common reasoning errors.
- Hint should suggest a strategy, not the answer.

### Forbidden

- No negative numbers.
- No algebra with letters.
- No content beyond the Grade 3 KICD sub-strand.
- No trick questions.
- No more than three steps.

### Example item

**Question:** What number goes in the box? □ + 6 = 15

- A) 7
- B) 8
- C) 9
- D) 10

**Correct answer:** C) 9

**Hint:** Work backwards: subtract 6 from 15.
