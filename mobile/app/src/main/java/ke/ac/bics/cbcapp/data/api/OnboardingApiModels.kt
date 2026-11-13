package ke.ac.bics.cbcapp.data.api

data class ProfileCreateDto(
    val studentId: String,
    val name: String
)

data class StudentProfileDto(
    val studentId: String,
    val name: String,
    val grade: String = "Grade 3",
    val className: String = "3A",
    val term: String = "Term 1",
    val competencyBand: String? = null,
    val bandStatus: String = "provisional",
    val placementCompleted: Boolean = false,
    val placementScore: Int? = null,
    val placementTotal: Int? = null,
    val placementPerBand: Map<String, Int> = emptyMap(),
    val xp: Int = 0,
    val streakDays: Int = 0,
    val dailyGoal: Int = 5
)

data class IntroQuizDto(
    val quizId: String,
    val version: Int,
    val title: String,
    val questionCount: Int,
    val generatedAt: String,
    val source: String,
    val questions: List<IntroQuestionDto>
)

data class IntroQuestionDto(
    val questionNumber: Int,
    val questionText: String,
    val options: List<String>,
    val band: String,
    val strand: String,
    val subStrand: String,
    val pedagogicalObjective: String
)

data class PlacementAnswerDto(
    val questionNumber: Int,
    val selectedOption: String
)

data class PlacementSubmissionDto(
    val quizId: String,
    val answers: List<PlacementAnswerDto>
)

data class PlacementResultDto(
    val quizId: String,
    val correct: Int,
    val total: Int,
    val perBand: Map<String, Int>,
    val band: String,
    val bandStatus: String,
    val teacherInsightSummary: String
)

data class PlacementResponseDto(
    val profile: StudentProfileDto,
    val result: PlacementResultDto
)
