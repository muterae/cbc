package ke.ac.bics.cbcapp.ui.screens.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ke.ac.bics.cbcapp.data.learner.LearnerRepository
import ke.ac.bics.cbcapp.data.session.SessionManager
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AuthViewModel(
    private val repository: LearnerRepository = LearnerRepository()
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    fun login(name: String, studentId: String) {
        val trimmedName = name.trim()
        val trimmedId = studentId.trim()
        if (trimmedName.isBlank() || trimmedId.isBlank()) {
            _uiState.value = AuthUiState(error = "Enter your name and student ID.")
            return
        }

        viewModelScope.launch {
            _uiState.value = AuthUiState(isLoading = true)
            try {
                val profile = repository.login(trimmedId, trimmedName)
                SessionManager.save(profile)
                _uiState.value = AuthUiState(profile = profile)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                _uiState.value = AuthUiState(
                    error = "Could not reach the server. Check that it is running and try again."
                )
            }
        }
    }
}
