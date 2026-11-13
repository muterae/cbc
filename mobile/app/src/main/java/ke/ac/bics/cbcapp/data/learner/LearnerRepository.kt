package ke.ac.bics.cbcapp.data.learner

import ke.ac.bics.cbcapp.data.api.ApiClient
import ke.ac.bics.cbcapp.data.api.IntroQuizDto
import ke.ac.bics.cbcapp.data.api.OnboardingApi
import ke.ac.bics.cbcapp.data.api.PlacementAnswerDto
import ke.ac.bics.cbcapp.data.api.PlacementResponseDto
import ke.ac.bics.cbcapp.data.api.PlacementSubmissionDto
import ke.ac.bics.cbcapp.data.api.ProfileCreateDto
import ke.ac.bics.cbcapp.data.api.StudentProfileDto
import retrofit2.HttpException

class LearnerRepository(
    private val api: OnboardingApi = ApiClient.onboardingApi
) {
    suspend fun login(studentId: String, name: String): StudentProfileDto {
        val existing = try {
            api.getProfile(studentId)
        } catch (e: HttpException) {
            if (e.code() == 404) null else throw e
        }
        return existing ?: api.createProfile(
            ProfileCreateDto(studentId = studentId, name = name)
        )
    }

    suspend fun getIntroQuiz(): IntroQuizDto = api.getIntroQuiz()

    suspend fun submitPlacement(
        studentId: String,
        quizId: String,
        answers: Map<Int, String>
    ): PlacementResponseDto = api.submitPlacement(
        studentId = studentId,
        request = PlacementSubmissionDto(
            quizId = quizId,
            answers = answers.map { (number, option) ->
                PlacementAnswerDto(questionNumber = number, selectedOption = option)
            }
        )
    )
}
