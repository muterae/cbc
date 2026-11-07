package ke.ac.bics.cbcapp.ui.screens.quiz

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ke.ac.bics.cbcapp.data.quiz.FakeQuizRepository
import ke.ac.bics.cbcapp.data.quiz.QuizRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class QuizViewModel(
    private val repository: QuizRepository = FakeQuizRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow<QuizUiState?>(null)
    val uiState: StateFlow<QuizUiState?> = _uiState.asStateFlow()

    init {
        load()
    }

    private fun load(subjectId: String = "math") {
        viewModelScope.launch {
            val quiz = repository.getQuiz(subjectId)
            _uiState.value = QuizUiState(quiz = quiz)
        }
    }

    fun selectOption(option: String) {
        val state = _uiState.value ?: return
        if (state.isChecked) return
        _uiState.value = state.copy(
            selectedOption = if (state.selectedOption == option) null else option
        )
    }

    fun useHint() {
        val state = _uiState.value ?: return
        if (!state.canUseHint) return
        _uiState.value = state.copy(hintUsed = state.hintUsed + state.currentIndex)
    }

    fun checkAnswer() {
        val state = _uiState.value ?: return
        val selected = state.selectedOption ?: return
        if (state.isChecked) return

        val result = QuestionResult(
            selectedOption = selected,
            isCorrect = selected == state.question.correctAnswer,
            hintUsed = state.hintVisible
        )
        val results = state.results.toMutableList().apply {
            this[state.currentIndex] = result
        }
        _uiState.value = state.copy(results = results, selectedOption = null)
    }

    fun next() {
        val state = _uiState.value ?: return
        if (!state.isChecked) return
        if (state.isLastQuestion) return
        _uiState.value = state.copy(currentIndex = state.currentIndex + 1)
    }

    fun previous() {
        val state = _uiState.value ?: return
        if (!state.canGoPrevious) return
        _uiState.value = state.copy(currentIndex = state.currentIndex - 1)
    }

    fun finish() {
        val state = _uiState.value ?: return
        if (state.results.any { it == null }) return
        _uiState.value = state.copy(
            isReviewing = true,
            currentIndex = 0,
            selectedOption = null
        )
    }

    fun restart() {
        val state = _uiState.value ?: return
        _uiState.value = state.copy(
            currentIndex = 0,
            selectedOption = null,
            hintUsed = emptySet(),
            results = List(state.totalQuestions) { null },
            isReviewing = false
        )
    }
}
