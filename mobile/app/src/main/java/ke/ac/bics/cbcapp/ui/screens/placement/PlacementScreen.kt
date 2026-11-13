package ke.ac.bics.cbcapp.ui.screens.placement

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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import ke.ac.bics.cbcapp.data.api.PlacementResultDto
import ke.ac.bics.cbcapp.ui.screens.quiz.components.AnswerOption
import ke.ac.bics.cbcapp.ui.screens.quiz.components.OptionState
import ke.ac.bics.cbcapp.ui.theme.Spacing

@Composable
fun PlacementScreen(
    onDone: () -> Unit,
    viewModel: PlacementViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    val result = state.result

    when {
        result != null -> PlacementResultContent(
            result = result,
            onDone = onDone
        )

        state.quiz == null -> PlacementStatusContent(
            error = state.error,
            onRetry = viewModel::load
        )

        else -> PlacementQuizContent(
            state = state,
            onSelect = viewModel::selectOption,
            onPrevious = viewModel::previous,
            onNext = viewModel::next,
            onSubmit = viewModel::submit
        )
    }
}

@Composable
private fun PlacementStatusContent(
    error: String?,
    onRetry: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentAlignment = Alignment.Center
    ) {
        if (error == null) {
            CircularProgressIndicator()
        } else {
            Column(
                modifier = Modifier.padding(Spacing.lg),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(Spacing.md)
            ) {
                Text(
                    text = error,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.error
                )
                Button(onClick = onRetry) {
                    Text("Retry")
                }
            }
        }
    }
}

@Composable
private fun PlacementQuizContent(
    state: PlacementUiState,
    onSelect: (String) -> Unit,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    onSubmit: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(Spacing.lg)
        ) {
            Text(
                text = "Placement quiz",
                style = MaterialTheme.typography.displaySmall
            )
            Spacer(modifier = Modifier.height(Spacing.xs))
            Text(
                text = "Question ${state.currentIndex + 1} of ${state.totalQuestions}",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(Spacing.lg))

            state.question?.let { question ->
                Text(
                    text = question.questionText,
                    style = MaterialTheme.typography.headlineMedium
                )

                Spacer(modifier = Modifier.height(Spacing.lg))

                question.options.forEach { option ->
                    AnswerOption(
                        text = option,
                        state = if (option == state.selectedOption) {
                            OptionState.Selected
                        } else {
                            OptionState.Default
                        },
                        enabled = !state.isSubmitting,
                        onClick = { onSelect(option) }
                    )
                    Spacer(modifier = Modifier.height(Spacing.md))
                }
            }
        }

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(Spacing.lg),
            verticalArrangement = Arrangement.spacedBy(Spacing.sm)
        ) {
            if (state.error != null) {
                Text(
                    text = state.error,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error
                )
            }

            Text(
                text = "${state.answeredCount} of ${state.totalQuestions} answered",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Row(verticalAlignment = Alignment.CenterVertically) {
                TextButton(
                    onClick = onPrevious,
                    enabled = state.canGoPrevious && !state.isSubmitting
                ) {
                    Text("Previous")
                }

                Spacer(modifier = Modifier.weight(1f))

                Button(
                    onClick = if (state.isLastQuestion) onSubmit else onNext,
                    enabled = !state.isSubmitting && if (state.isLastQuestion) {
                        state.allAnswered
                    } else {
                        state.selectedOption != null
                    },
                    modifier = Modifier.weight(1f)
                ) {
                    if (state.isSubmitting) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            color = MaterialTheme.colorScheme.onPrimary,
                            strokeWidth = 2.dp
                        )
                    } else {
                        Text(if (state.isLastQuestion) "Submit" else "Next")
                    }
                }
            }
        }
    }
}

@Composable
private fun PlacementResultContent(
    result: PlacementResultDto,
    onDone: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .verticalScroll(rememberScrollState())
            .padding(Spacing.lg),
        verticalArrangement = Arrangement.spacedBy(Spacing.md)
    ) {
        Text(
            text = "Placement complete",
            style = MaterialTheme.typography.displaySmall
        )
        Text(
            text = "Your provisional band",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = result.band,
            style = MaterialTheme.typography.headlineMedium
        )
        Text(
            text = "${result.correct} of ${result.total} correct",
            style = MaterialTheme.typography.bodyLarge
        )
        Text(
            text = result.teacherInsightSummary,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(Spacing.sm))
        Text(
            text = "By band",
            style = MaterialTheme.typography.titleLarge
        )
        result.perBand.forEach { (code, score) ->
            Row(modifier = Modifier.fillMaxWidth()) {
                Text(text = bandLabel(code), style = MaterialTheme.typography.bodyLarge)
                Spacer(modifier = Modifier.weight(1f))
                Text(text = "$score / 3", style = MaterialTheme.typography.bodyLarge)
            }
        }

        Spacer(modifier = Modifier.height(Spacing.md))
        Text(
            text = "This band is provisional. Your teacher will confirm it later.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Button(
            onClick = onDone,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Continue")
        }
    }
}

private fun bandLabel(code: String): String = when (code) {
    "BE" -> "Below Expectation"
    "AE" -> "Approaching Expectation"
    "ME" -> "Meeting Expectation"
    "EE" -> "Exceeding Expectation"
    else -> code
}
