package ke.ac.bics.cbcapp.ui.screens.profile

import ke.ac.bics.cbcapp.data.api.StudentProfileDto

data class ProfileUiState(
    val name: String,
    val studentId: String,
    val grade: String,
    val streakDays: Int,
    val xp: Int
) {
    val initial: String
        get() = name.take(1).uppercase()
}

/** Placeholder content until the server provides real data. */
fun sampleProfileState() = ProfileUiState(
    name = "Amina",
    studentId = "std_ke_09823",
    grade = "Grade 3",
    streakDays = 4,
    xp = 280
)

fun StudentProfileDto.toProfileUiState() = ProfileUiState(
    name = name,
    studentId = studentId,
    grade = grade,
    streakDays = streakDays,
    xp = xp
)
