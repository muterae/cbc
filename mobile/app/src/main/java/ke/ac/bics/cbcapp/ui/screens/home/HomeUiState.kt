package ke.ac.bics.cbcapp.ui.screens.home

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Calculate
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.Science
import androidx.compose.ui.graphics.vector.ImageVector

data class SubjectProgress(
    val id: String,
    val name: String,
    val description: String,
    val icon: ImageVector,
    val answeredToday: Int,
    val dailyGoal: Int
) {
    val progress: Float
        get() = (answeredToday.toFloat() / dailyGoal).coerceIn(0f, 1f)
}

data class LeaderboardEntry(
    val rank: Int,
    val name: String,
    val xp: Int,
    val isCurrentUser: Boolean = false
)

data class HomeUiState(
    val greetingName: String,
    val streakDays: Int,
    val subjects: List<SubjectProgress>,
    val leaderboard: List<LeaderboardEntry>
)

/** Placeholder content until the server provides real data. */
fun sampleHomeState() = HomeUiState(
    greetingName = "Amina",
    streakDays = 4,
    subjects = listOf(
        SubjectProgress(
            id = "math",
            name = "Mathematics",
            description = "Numbers, shapes and patterns",
            icon = Icons.Rounded.Calculate,
            answeredToday = 3,
            dailyGoal = 5
        ),
        SubjectProgress(
            id = "english",
            name = "English",
            description = "Reading, writing and listening",
            icon = Icons.AutoMirrored.Rounded.MenuBook,
            answeredToday = 2,
            dailyGoal = 5
        ),
        SubjectProgress(
            id = "science",
            name = "Science",
            description = "Plants, animals and materials",
            icon = Icons.Rounded.Science,
            answeredToday = 1,
            dailyGoal = 5
        )
    ),
    leaderboard = listOf(
        LeaderboardEntry(rank = 1, name = "Brian", xp = 320),
        LeaderboardEntry(rank = 2, name = "Amina", xp = 280, isCurrentUser = true),
        LeaderboardEntry(rank = 3, name = "Wanjiku", xp = 240),
        LeaderboardEntry(rank = 4, name = "Otieno", xp = 190),
        LeaderboardEntry(rank = 5, name = "Zawadi", xp = 150)
    )
)
