package ke.ac.bics.cbcapp.data.quiz

import android.util.Log
import ke.ac.bics.cbcapp.data.api.AdaptiveQuizRequestDto
import ke.ac.bics.cbcapp.data.api.AdaptiveQuizResponseDto
import ke.ac.bics.cbcapp.data.api.ApiClient
import ke.ac.bics.cbcapp.data.api.ApiConfig
import ke.ac.bics.cbcapp.data.api.CbcApi
import ke.ac.bics.cbcapp.data.api.QuizQuestionDto
import ke.ac.bics.cbcapp.data.session.SessionManager
import kotlinx.coroutines.CancellationException

/**
 * Fetches an adaptive quiz from the FastAPI server.
 *
 * The quiz is requested for the signed-in learner. If there is no session yet,
 * the seeded demo learner is used. If the server is unreachable or rejects the
 * request, the local sample quiz keeps the app usable.
 */
class RemoteQuizRepository(
    private val api: CbcApi = ApiClient.api,
    private val studentId: String? = null
) : QuizRepository {

    override suspend fun getQuiz(subjectId: String): Quiz {
        return try {
            val response = api.adaptiveQuiz(
                AdaptiveQuizRequestDto(
                    studentId = studentId
                        ?: SessionManager.studentId
                        ?: ApiConfig.DEMO_STUDENT_ID,
                    strand = if (subjectId.equals("math", ignoreCase = true)) {
                        "Mathematics"
                    } else {
                        subjectId
                    }
                )
            )
            if (response.questions.isEmpty()) sampleQuiz else response.toQuiz()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            Log.w(TAG, "Server quiz unavailable; using local sample.", e)
            sampleQuiz
        }
    }

    private fun AdaptiveQuizResponseDto.toQuiz() = Quiz(
        competencyBand = competencyBand,
        strand = strand,
        questions = questions.map { it.toQuizQuestion() },
        teacherInsightSummary = teacherInsightSummary
    )

    private fun QuizQuestionDto.toQuizQuestion() = QuizQuestion(
        questionText = questionText,
        options = options,
        correctAnswer = correctAnswer,
        hint = hint
    )

    private companion object {
        const val TAG = "RemoteQuizRepository"
    }
}
