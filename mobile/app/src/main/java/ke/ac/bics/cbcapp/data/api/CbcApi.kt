package ke.ac.bics.cbcapp.data.api

import retrofit2.http.Body
import retrofit2.http.POST

interface CbcApi {
    @POST("api/v1/adaptive-quiz")
    suspend fun adaptiveQuiz(@Body request: AdaptiveQuizRequestDto): AdaptiveQuizResponseDto
}
