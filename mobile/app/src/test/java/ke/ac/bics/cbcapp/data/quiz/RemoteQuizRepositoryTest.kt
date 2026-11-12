package ke.ac.bics.cbcapp.data.quiz

import ke.ac.bics.cbcapp.data.api.AdaptiveQuizRequestDto
import ke.ac.bics.cbcapp.data.api.AdaptiveQuizResponseDto
import ke.ac.bics.cbcapp.data.api.CbcApi
import ke.ac.bics.cbcapp.data.api.QuizQuestionDto
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RemoteQuizRepositoryTest {

    @Test
    fun mapsServerResponseToDomainQuiz() = runBlocking {
        val api = object : CbcApi {
            override suspend fun adaptiveQuiz(
                request: AdaptiveQuizRequestDto
            ): AdaptiveQuizResponseDto {
                assertEquals("std_ke_09823", request.studentId)
                assertEquals("Mathematics", request.strand)
                return AdaptiveQuizResponseDto(
                    strand = "Numbers - Addition",
                    competencyBand = "Approaching Expectation",
                    questions = listOf(
                        QuizQuestionDto(
                            questionNumber = 1,
                            questionText = "What is 2 + 2?",
                            options = listOf("A) 3", "B) 4"),
                            correctAnswer = "B) 4",
                            hint = "Count two more.",
                            pedagogicalObjective = "Add within 10."
                        )
                    ),
                    teacherInsightSummary = "Practising addition."
                )
            }
        }

        val quiz = RemoteQuizRepository(api = api).getQuiz("math")

        assertEquals("Approaching Expectation", quiz.competencyBand)
        assertEquals("Numbers - Addition", quiz.strand)
        assertEquals("What is 2 + 2?", quiz.questions.single().questionText)
        assertEquals("B) 4", quiz.questions.single().correctAnswer)
    }

    @Test
    fun fallsBackToSampleWhenServerFails() = runBlocking {
        val api = object : CbcApi {
            override suspend fun adaptiveQuiz(
                request: AdaptiveQuizRequestDto
            ): AdaptiveQuizResponseDto {
                error("offline")
            }
        }

        val quiz = RemoteQuizRepository(api = api).getQuiz("math")

        assertEquals(sampleQuiz, quiz)
        assertTrue(quiz.questions.isNotEmpty())
    }
}
