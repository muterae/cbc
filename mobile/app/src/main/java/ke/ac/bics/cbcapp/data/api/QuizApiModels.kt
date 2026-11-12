package ke.ac.bics.cbcapp.data.api

data class AdaptiveQuizRequestDto(
    val studentId: String,
    val strand: String = "Mathematics",
    val subStrand: String? = null,
    val sessionType: String = "practice"
)

data class AdaptiveQuizResponseDto(
    val strand: String,
    val competencyBand: String,
    val questions: List<QuizQuestionDto>,
    val teacherInsightSummary: String
)

data class QuizQuestionDto(
    val questionNumber: Int,
    val questionText: String,
    val options: List<String>,
    val correctAnswer: String,
    val hint: String,
    val pedagogicalObjective: String
)
