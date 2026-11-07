package ke.ac.bics.cbcapp.ui.screens.quiz.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Lightbulb
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

@Composable
fun QuizHeader(
    currentNumber: Int,
    totalQuestions: Int,
    answeredQuestions: Int,
    isReviewing: Boolean,
    correctCount: Int,
    canUseHint: Boolean,
    onExit: () -> Unit,
    onHint: () -> Unit,
    modifier: Modifier = Modifier
) {
    val colors = MaterialTheme.colorScheme

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onExit) {
                Icon(
                    imageVector = Icons.Rounded.Close,
                    contentDescription = "Leave quiz",
                    tint = colors.onSurface
                )
            }

            Text(
                text = if (isReviewing) {
                    "$correctCount of $totalQuestions correct"
                } else {
                    "Question $currentNumber of $totalQuestions"
                },
                style = MaterialTheme.typography.titleMedium,
                textAlign = TextAlign.Center,
                modifier = Modifier.weight(1f)
            )

            IconButton(onClick = onHint, enabled = canUseHint) {
                Icon(
                    imageVector = Icons.Rounded.Lightbulb,
                    contentDescription = "Show hint",
                    tint = if (canUseHint) colors.primary else colors.onSurfaceVariant.copy(alpha = 0.4f)
                )
            }
        }

        Spacer(modifier = Modifier.height(4.dp))

        LinearProgressIndicator(
            progress = {
                if (totalQuestions == 0) 0f
                else answeredQuestions.toFloat() / totalQuestions
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(12.dp),
            color = colors.primary,
            trackColor = colors.outlineVariant,
            strokeCap = StrokeCap.Round
        )
    }
}
