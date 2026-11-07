package ke.ac.bics.cbcapp.ui.screens.quiz

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.collectAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import ke.ac.bics.cbcapp.data.quiz.sampleQuiz
import ke.ac.bics.cbcapp.ui.screens.quiz.components.AnswerOption
import ke.ac.bics.cbcapp.ui.screens.quiz.components.HintCard
import ke.ac.bics.cbcapp.ui.screens.quiz.components.OptionState
import ke.ac.bics.cbcapp.ui.screens.quiz.components.QuizHeader
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme
import ke.ac.bics.cbcapp.ui.theme.Spacing

@Composable
fun QuizScreen(
    onExit: () -> Unit,
    viewModel: QuizViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    var showLeaveDialog by rememberSaveable { mutableStateOf(false) }

    BackHandler { showLeaveDialog = true }

    val current = state
    if (current == null) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background),
            contentAlignment = Alignment.Center
        ) {
            CircularProgressIndicator()
        }
        return
    }

    QuizContent(
        state = current,
        onExit = { showLeaveDialog = true },
        onHint = viewModel::useHint,
        onSelect = viewModel::selectOption,
        onPrevious = viewModel::previous,
        onPrimary = {
            when {
                !current.isChecked -> viewModel.checkAnswer()
                current.isReviewing && current.isLastQuestion -> viewModel.restart()
                !current.isReviewing && current.isLastQuestion -> viewModel.finish()
                else -> viewModel.next()
            }
        }
    )

    if (showLeaveDialog) {
        AlertDialog(
            onDismissRequest = { showLeaveDialog = false },
            title = { Text("Leave quiz?") },
            text = { Text("Your progress will be lost.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        showLeaveDialog = false
                        onExit()
                    }
                ) {
                    Text("Leave")
                }
            },
            dismissButton = {
                TextButton(onClick = { showLeaveDialog = false }) {
                    Text("Stay")
                }
            }
        )
    }
}

@Composable
private fun QuizContent(
    state: QuizUiState,
    onExit: () -> Unit,
    onHint: () -> Unit,
    onSelect: (String) -> Unit,
    onPrevious: () -> Unit,
    onPrimary: () -> Unit
) {
    val colors = MaterialTheme.colorScheme

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(colors.background)
    ) {
        QuizHeader(
            currentNumber = state.currentIndex + 1,
            totalQuestions = state.totalQuestions,
            answeredQuestions = state.answeredCount,
            isReviewing = state.isReviewing,
            correctCount = state.correctCount,
            canUseHint = state.canUseHint,
            onExit = onExit,
            onHint = onHint,
            modifier = Modifier.padding(horizontal = Spacing.sm, vertical = Spacing.sm)
        )

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = Spacing.lg)
        ) {
            Spacer(modifier = Modifier.height(Spacing.md))

            Text(
                text = state.question.questionText,
                style = MaterialTheme.typography.headlineMedium
            )

            Spacer(modifier = Modifier.height(Spacing.lg))

            state.question.options.forEach { option ->
                AnswerOption(
                    text = option,
                    state = optionState(option, state),
                    enabled = !state.isChecked,
                    onClick = { onSelect(option) }
                )
                Spacer(modifier = Modifier.height(Spacing.md))
            }

            if (state.hintVisible && state.question.hint.isNotBlank()) {
                Spacer(modifier = Modifier.height(Spacing.xs))
                HintCard(hint = state.question.hint)
            }

            Spacer(modifier = Modifier.height(Spacing.xl))
        }

        QuizFooter(
            state = state,
            onPrevious = onPrevious,
            onPrimary = onPrimary,
            onExit = onExit
        )
    }
}

@Composable
private fun QuizFooter(
    state: QuizUiState,
    onPrevious: () -> Unit,
    onPrimary: () -> Unit,
    onExit: () -> Unit
) {
    val primaryLabel = when {
        !state.isChecked -> "Check"
        state.isReviewing && state.isLastQuestion -> "Play again"
        !state.isReviewing && state.isLastQuestion -> "Finish"
        else -> "Next"
    }
    val primaryEnabled = if (state.isChecked) true else state.selectedOption != null

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = Spacing.lg, vertical = Spacing.md),
        verticalArrangement = Arrangement.spacedBy(Spacing.sm)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(
                onClick = onPrevious,
                enabled = state.canGoPrevious
            ) {
                Text("Previous")
            }

            Spacer(modifier = Modifier.weight(1f))

            Button(
                onClick = onPrimary,
                enabled = primaryEnabled,
                modifier = Modifier.weight(1f)
            ) {
                Text(primaryLabel)
            }
        }

        if (state.isReviewing && state.isLastQuestion) {
            OutlinedButton(
                onClick = onExit,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Back to Home")
            }
        }
    }
}

private fun optionState(option: String, state: QuizUiState): OptionState {
    val result = state.result
    return when {
        result == null ->
            if (option == state.selectedOption) OptionState.Selected else OptionState.Default

        state.isReviewing -> when (option) {
            state.question.correctAnswer -> OptionState.Correct
            result.selectedOption -> OptionState.Wrong
            else -> OptionState.Muted
        }

        else -> when (option) {
            result.selectedOption ->
                if (result.isCorrect) OptionState.Correct else OptionState.Wrong
            else -> OptionState.Muted
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun QuizContentPreview() {
    CbcappTheme {
        QuizContent(
            state = QuizUiState(quiz = sampleQuiz),
            onExit = {},
            onHint = {},
            onSelect = {},
            onPrevious = {},
            onPrimary = {}
        )
    }
}
