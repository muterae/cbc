package ke.ac.bics.cbcapp.ui.screens.placement

import ke.ac.bics.cbcapp.data.api.IntroQuestionDto
import ke.ac.bics.cbcapp.data.api.IntroQuizDto
import ke.ac.bics.cbcapp.data.api.PlacementResultDto

data class PlacementUiState(
    val quiz: IntroQuizDto? = null,
    val currentIndex: Int = 0,
    val answers: Map<Int, String> = emptyMap(),
    val isSubmitting: Boolean = false,
    val error: String? = null,
    val result: PlacementResultDto? = null
) {
    val question: IntroQuestionDto? get() = quiz?.questions?.getOrNull(currentIndex)
    val totalQuestions: Int get() = quiz?.questions?.size ?: 0
    val answeredCount: Int get() = answers.size
    val selectedOption: String? get() = question?.let { answers[it.questionNumber] }
    val canGoPrevious: Boolean get() = currentIndex > 0
    val isLastQuestion: Boolean get() = quiz?.questions?.lastIndex == currentIndex
    val allAnswered: Boolean get() = quiz?.questions?.size?.let { answers.size == it } == true
}
