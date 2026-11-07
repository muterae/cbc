package ke.ac.bics.cbcapp.ui.screens.quiz.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import ke.ac.bics.cbcapp.ui.theme.cbcColors

enum class OptionState {
    Default,
    Selected,
    Correct,
    Wrong,
    Muted
}

@Composable
fun AnswerOption(
    text: String,
    state: OptionState,
    enabled: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val colors = MaterialTheme.colorScheme
    val cbc = MaterialTheme.cbcColors

    val container: Color
    val content: Color
    when (state) {
        OptionState.Default -> {
            container = colors.surface
            content = colors.onSurface
        }
        OptionState.Selected -> {
            container = colors.primaryContainer
            content = colors.onPrimaryContainer
        }
        OptionState.Correct -> {
            container = cbc.success
            content = cbc.onSuccess
        }
        OptionState.Wrong -> {
            container = colors.errorContainer
            content = colors.onErrorContainer
        }
        OptionState.Muted -> {
            container = colors.surfaceVariant.copy(alpha = 0.5f)
            content = colors.onSurfaceVariant.copy(alpha = 0.6f)
        }
    }

    val border = when (state) {
        OptionState.Default -> BorderStroke(1.dp, colors.outline)
        OptionState.Selected -> BorderStroke(2.dp, colors.primary)
        OptionState.Correct -> BorderStroke(2.dp, cbc.success)
        OptionState.Wrong -> BorderStroke(2.dp, colors.error)
        OptionState.Muted -> null
    }

    val trailing: ImageVector? = when (state) {
        OptionState.Correct -> Icons.Rounded.Check
        OptionState.Wrong -> Icons.Rounded.Close
        else -> null
    }

    Surface(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        color = container,
        contentColor = content,
        border = border
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.weight(1f)
            )
            if (trailing != null) {
                Icon(
                    imageVector = trailing,
                    contentDescription = null,
                    modifier = Modifier.size(24.dp)
                )
            }
        }
    }
}
