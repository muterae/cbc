package ke.ac.bics.cbcapp.data.quiz

interface QuizRepository {
    suspend fun getQuiz(subjectId: String): Quiz
}
