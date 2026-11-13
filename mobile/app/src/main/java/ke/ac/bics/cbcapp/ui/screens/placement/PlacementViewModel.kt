package ke.ac.bics.cbcapp.ui.screens.placement

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ke.ac.bics.cbcapp.data.learner.LearnerRepository
import ke.ac.bics.cbcapp.data.session.SessionManager
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class PlacementViewModel(
    private val repository: LearnerRepository = LearnerRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow(PlacementUiState())
    val uiState: StateFlow<PlacementUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        val studentId = SessionManager.studentId
        if (studentId == null) {
            _uiState.value = PlacementUiState(
                error = "Please log in again to start the placement quiz."
            )
            return
        }

        viewModelScope.launch {
            _uiState.value = PlacementUiState()
            try {
                val quiz = repository.getIntroQuiz()
                _uiState.value = PlacementUiState(quiz = quiz)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                _uiState.value = PlacementUiState(
                    error = "Could not load the placement quiz. Check the server and retry."
                )
            }
        }
    }

    fun selectOption(option: String) {
        val state = _uiState.value
        val question = state.question ?: return
        _uiState.value = state.copy(
            answers = state.answers + (question.questionNumber to option),
            error = null
        )
    }

    fun next() {
        val state = _uiState.value
        if (state.isLastQuestion) return
        _uiState.value = state.copy(currentIndex = state.currentIndex + 1)
    }

    fun previous() {
        val state = _uiState.value
        if (!state.canGoPrevious) return
        _uiState.value = state.copy(currentIndex = state.currentIndex - 1)
    }

    fun submit() {
        val state = _uiState.value
        val quiz = state.quiz ?: return
        val studentId = SessionManager.studentId ?: return
        if (!state.allAnswered || state.isSubmitting) return

        viewModelScope.launch {
            _uiState.value = state.copy(isSubmitting = true, error = null)
            try {
                val response = repository.submitPlacement(
                    studentId = studentId,
                    quizId = quiz.quizId,
                    answers = state.answers
                )
                SessionManager.save(response.profile)
                _uiState.value = state.copy(
                    isSubmitting = false,
                    result = response.result
                )
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                _uiState.value = state.copy(
                    isSubmitting = false,
                    error = "Could not submit your answers. Check the server and retry."
                )
            }
        }
    }
}
