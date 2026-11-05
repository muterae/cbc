package ke.ac.bics.cbcapp.ui.screens.home

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.LocalFireDepartment
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import ke.ac.bics.cbcapp.ui.screens.home.components.LeaderboardCard
import ke.ac.bics.cbcapp.ui.screens.home.components.ProgressRing
import ke.ac.bics.cbcapp.ui.screens.home.components.SubjectCard
import ke.ac.bics.cbcapp.ui.theme.BrandPurple
import ke.ac.bics.cbcapp.ui.theme.BrandPurpleLight
import ke.ac.bics.cbcapp.ui.theme.CbcappTheme
import ke.ac.bics.cbcapp.ui.theme.Spacing
import ke.ac.bics.cbcapp.ui.theme.SuccessGreen
import ke.ac.bics.cbcapp.ui.theme.SuccessGreenStroke
import ke.ac.bics.cbcapp.ui.theme.WarningDark
import ke.ac.bics.cbcapp.ui.theme.WarningLight
import ke.ac.bics.cbcapp.ui.theme.cbcColors
import kotlin.math.roundToInt

@Composable
fun HomeScreen(
    state: HomeUiState = sampleHomeState(),
    onSubjectClick: (SubjectProgress) -> Unit = {}
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = PaddingValues(
            start = Spacing.lg,
            end = Spacing.lg,
            top = Spacing.lg,
            bottom = Spacing.xl
        ),
        verticalArrangement = Arrangement.spacedBy(Spacing.lg)
    ) {
        item {
            Greeting(state.greetingName)
        }

        item {
            Spacer(modifier = Modifier.height(Spacing.lg))
            ProgressCard(state)
        }

        item {
            SectionTitle("Subjects")
        }

        items(state.subjects) { subject ->
            SubjectCard(
                subject = subject,
                onClick = { onSubjectClick(subject) }
            )
        }

        item {
            SectionTitle("Leaderboard")
        }

        item {
            LeaderboardCard(entries = state.leaderboard)
        }
    }
}

@Composable
private fun Greeting(name: String) {
    Column {
        Text(
            text = "Hi, $name",
            style = MaterialTheme.typography.displaySmall
        )
        Text(
            text = "Ready for today's quiz?",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun ProgressCard(state: HomeUiState) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.background
        )
    ) {
        Column(modifier = Modifier.padding(Spacing.lg)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Rounded.LocalFireDepartment,
                    contentDescription = null,
                    tint = MaterialTheme.cbcColors.warning
                )
                Spacer(modifier = Modifier.width(Spacing.sm))
                Text(
                    text = "${state.streakDays} day streak",
                    style = MaterialTheme.typography.titleLarge
                )
            }

            Spacer(modifier = Modifier.height(Spacing.lg))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                state.subjects.forEach { subject ->
                    SubjectRing(subject)
                }
            }
        }
    }
}

@Composable
private fun SubjectRing(subject: SubjectProgress) {
    val accent = ringColor(subject.id)
    val isComplete = subject.progress >= 1f

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(contentAlignment = Alignment.Center) {
            ProgressRing(
                progress = subject.progress,
                color = accent,
                label = subject.name,
                modifier = Modifier.size(96.dp),
                strokeWidth = 12.dp
            )
            if (isComplete) {
                Icon(
                    imageVector = Icons.Rounded.Check,
                    contentDescription = null,
                    tint = accent,
                    modifier = Modifier.size(32.dp)
                )
            } else {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(Spacing.sm)
                ){
                    Text(
                        text = "${(subject.progress * 100).roundToInt()}",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text="${subject.name}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }

            }
        }

    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleLarge,
        modifier = Modifier.padding(top = Spacing.sm)
    )
}

@Composable
private fun ringColor(subjectId: String): Color {
    val dark = isSystemInDarkTheme()
    return when (subjectId) {
        "math" -> if (dark) BrandPurpleLight else BrandPurple
        "english" -> if (dark) SuccessGreen else SuccessGreenStroke
        "science" -> if (dark) WarningDark else WarningLight
        else -> MaterialTheme.colorScheme.primary
    }
}

@Preview(showBackground = true)
@Composable
private fun HomeScreenPreview() {
    CbcappTheme {
        HomeScreen()
    }
}

@Preview(showBackground = true, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun HomeScreenDarkPreview() {
    CbcappTheme {
        HomeScreen()
    }
}
