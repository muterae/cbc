# Quiz

Single screen used for both answering and review. Bottom bar is hidden on this route.

| File | Role |
|---|---|
| `QuizScreen.kt` | Layout, footer actions, leave dialog |
| `QuizUiState.kt` | `QuestionResult`, per-question state derived values |
| `QuizViewModel.kt` | Select, check, next/previous, finish, restart |
| `components/QuizHeader.kt` | Counter, progress bar, X and hint buttons |
| `components/AnswerOption.kt` | Option states |
| `components/HintCard.kt` | Hint panel |
| `data/quiz/*` | `Quiz`/`QuizQuestion`, repository + fake quiz |

## Answer flow

1. `Answering`: tap selects (tap again deselects). `Check` is disabled until something is selected.
2. `Check`: records `QuestionResult`, locks the question, fills the progress bar. The correct
   answer is **not** revealed.
3. `Next` / `Previous`: free navigation. Checked questions stay read-only.
4. After the last question, `Finish` enters `Review` at question 1 with the score in the header.
5. Review shows correct answers in green; wrong picks stay red; the rest are muted.
   Last review step offers `Play again` and `Back to Home`.

Hints are stored per question (`hintUsed`) and stay visible when you return to that question.
The hint button is disabled after use or when the hint is empty.

Colours: correct = success green, wrong = destructive, unselected = muted 40%.
The X button and system back both open a "Leave quiz?" dialog.
