package ke.ac.bics.cbcapp.data.quiz

/**
 * Local quiz used until the mobile client is wired to POST /api/v1/adaptive-quiz.
 * Option strings keep the server's "A) ..." prefix so the swap to a remote
 * repository will not change the UI.
 */
class FakeQuizRepository : QuizRepository {

    override suspend fun getQuiz(subjectId: String): Quiz = sampleQuiz
}

val sampleQuiz = Quiz(
    competencyBand = "Meeting Expectation",
    strand = "Numbers - Addition",
    teacherInsightSummary = "Learner is comfortable with single-step addition using familiar objects.",
    questions = listOf(
        QuizQuestion(
            questionText = "Amina has 12 mangoes. She buys 5 more. How many mangoes does she have now?",
            options = listOf("A) 15", "B) 16", "C) 17", "D) 18"),
            correctAnswer = "C) 17",
            hint = "Count 5 steps forward starting from 12."
        ),
        QuizQuestion(
            questionText = "There are 20 pupils in a class. 8 are girls. How many are boys?",
            options = listOf("A) 10", "B) 11", "C) 12", "D) 13"),
            correctAnswer = "C) 12",
            hint = "Take away the girls from the whole class."
        ),
        QuizQuestion(
            questionText = "Which shape has 3 sides?",
            options = listOf("A) Circle", "B) Triangle", "C) Square", "D) Rectangle"),
            correctAnswer = "B) Triangle",
            hint = "Tri means three."
        ),
        QuizQuestion(
            questionText = "What is 7 x 3?",
            options = listOf("A) 10", "B) 21", "C) 24", "D) 18"),
            correctAnswer = "B) 21",
            hint = "Add 7 three times: 7 + 7 + 7."
        ),
        QuizQuestion(
            questionText = "A pencil costs 5 shillings. How much do 4 pencils cost?",
            options = listOf("A) 15", "B) 20", "C) 25", "D) 9"),
            correctAnswer = "B) 20",
            hint = "Add 5 four times."
        )
    )
)
