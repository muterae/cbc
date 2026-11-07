package ke.ac.bics.cbcapp.data.quiz

data class QuizQuestion(
    val questionText: String,
    val options: List<String>,
    val correctAnswer: String,
    val hint: String
)

data class Quiz(
    val competencyBand: String,
    val strand: String,
    val questions: List<QuizQuestion>,
    val teacherInsightSummary: String
)
