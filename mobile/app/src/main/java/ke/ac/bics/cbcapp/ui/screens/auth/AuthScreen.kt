package ke.ac.bics.cbcapp.ui.screens.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import ke.ac.bics.cbcapp.data.api.StudentProfileDto
import ke.ac.bics.cbcapp.data.session.SessionManager
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme
import ke.ac.bics.cbcapp.ui.theme.Spacing

@Composable
fun AuthScreen(
    onLoggedIn: (StudentProfileDto) -> Unit,
    viewModel: AuthViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    var name by rememberSaveable { mutableStateOf(SessionManager.studentName.orEmpty()) }
    var studentId by rememberSaveable { mutableStateOf(SessionManager.studentId.orEmpty()) }

    LaunchedEffect(state.profile) {
        state.profile?.let(onLoggedIn)
    }

    AuthContent(
        name = name,
        studentId = studentId,
        isLoading = state.isLoading,
        error = state.error,
        onNameChange = { name = it },
        onStudentIdChange = { studentId = it },
        onLogin = { viewModel.login(name, studentId) }
    )
}

@Composable
private fun AuthContent(
    name: String,
    studentId: String,
    isLoading: Boolean,
    error: String?,
    onNameChange: (String) -> Unit,
    onStudentIdChange: (String) -> Unit,
    onLogin: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(Spacing.lg),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "CBC Learning Companion",
            style = MaterialTheme.typography.displaySmall
        )
        Spacer(modifier = Modifier.height(Spacing.sm))
        Text(
            text = "Enter your name and student ID. No password needed.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(Spacing.xl))

        OutlinedTextField(
            value = name,
            onValueChange = onNameChange,
            label = { Text("Name") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(Spacing.md))

        OutlinedTextField(
            value = studentId,
            onValueChange = onStudentIdChange,
            label = { Text("Student ID") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Ascii),
            modifier = Modifier.fillMaxWidth()
        )

        if (error != null) {
            Spacer(modifier = Modifier.height(Spacing.md))
            Text(
                text = error,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error
            )
        }

        Spacer(modifier = Modifier.height(Spacing.lg))

        Button(
            onClick = onLogin,
            enabled = !isLoading && name.isNotBlank() && studentId.isNotBlank(),
            modifier = Modifier.fillMaxWidth()
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(18.dp),
                    color = MaterialTheme.colorScheme.onPrimary,
                    strokeWidth = 2.dp
                )
            } else {
                Text("Log in")
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun AuthScreenPreview() {
    CbcappTheme {
        AuthContent(
            name = "Amina",
            studentId = "std_ke_09823",
            isLoading = false,
            error = null,
            onNameChange = {},
            onStudentIdChange = {},
            onLogin = {}
        )
    }
}
