package ke.ac.bics.cbcapp.ui.screens.quiz

import ke.ac.bics.cbcapp.data.quiz.Quiz
import ke.ac.bics.cbcapp.data.quiz.QuizQuestion

data class QuestionResult(
    val selectedOption: String,
    val isCorrect: Boolean,
    val hintUsed: Boolean
)

data class QuizUiState(
    val quiz: Quiz,
    val currentIndex: Int = 0,
    val selectedOption: String? = null,
    val hintUsed: Set<Int> = emptySet(),
    val results: List<QuestionResult?> = List(quiz.questions.size) { null },
    val isReviewing: Boolean = false
) {
    val questions: List<QuizQuestion> get() = quiz.questions
    val question: QuizQuestion get() = questions[currentIndex]
    val result: QuestionResult? get() = results[currentIndex]
    val isChecked: Boolean get() = result != null
    val totalQuestions: Int get() = questions.size
    val answeredCount: Int get() = results.count { it != null }
    val correctCount: Int get() = results.count { it?.isCorrect == true }
    val isLastQuestion: Boolean get() = currentIndex == questions.lastIndex
    val canGoPrevious: Boolean get() = currentIndex > 0
    val hintVisible: Boolean get() = currentIndex in hintUsed
    val canUseHint: Boolean get() = !isChecked && !hintVisible && question.hint.isNotBlank()
}
