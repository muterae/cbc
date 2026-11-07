package ke.ac.bics.cbcapp.ui.screens.profile.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.LocalFireDepartment
import androidx.compose.material.icons.rounded.Star
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import ke.ac.bics.cbcapp.ui.screens.profile.ProfileUiState
import ke.ac.bics.cbcapp.ui.theme.Spacing

@Composable
fun ProfileHeaderCard(
    state: ProfileUiState,
    modifier: Modifier = Modifier
) {
    val colors = MaterialTheme.colorScheme

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = colors.surface)
    ) {
        Column(modifier = Modifier.padding(Spacing.lg)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(64.dp)
                        .background(colors.primaryContainer, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = state.initial,
                        style = MaterialTheme.typography.headlineSmall,
                        color = colors.onPrimaryContainer
                    )
                }

                Spacer(modifier = Modifier.width(Spacing.lg))
                Spacer(modifier = Modifier.width(Spacing.lg))
                Spacer(modifier = Modifier.width(Spacing.lg))

                Column {
                    Text(
                        text = state.name,
                        style = MaterialTheme.typography.titleLarge
                    )
                    Text(
                        text = "${state.studentId} · ${state.grade}",
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(Spacing.lg))
            Spacer(modifier = Modifier.width(Spacing.lg))
            Spacer(modifier = Modifier.width(Spacing.lg))

            Row(horizontalArrangement = Arrangement.spacedBy(Spacing.sm)) {
                StatChip(
                    icon = Icons.Rounded.LocalFireDepartment,
                    label = "${state.streakDays} day streak"
                )
                StatChip(
                    icon = Icons.Rounded.Star,
                    label = "${state.xp} XP"
                )
            }
        }
    }
}

@Composable
private fun StatChip(
    icon: ImageVector,
    label: String
) {
    val colors = MaterialTheme.colorScheme

    Surface(
        shape = CircleShape,
        color = colors.surfaceVariant
    ) {
        Row(
            modifier = Modifier.padding(horizontal = Spacing.md, vertical = Spacing.xs + 2.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(Spacing.xs)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = colors.onSurfaceVariant,
                modifier = Modifier.size(16.dp)
            )
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                color = colors.onSurfaceVariant
            )
        }
    }
}
