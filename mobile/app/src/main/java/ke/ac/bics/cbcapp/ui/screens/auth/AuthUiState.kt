package ke.ac.bics.cbcapp.ui.screens.auth

import ke.ac.bics.cbcapp.data.api.StudentProfileDto

data class AuthUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val profile: StudentProfileDto? = null
)
