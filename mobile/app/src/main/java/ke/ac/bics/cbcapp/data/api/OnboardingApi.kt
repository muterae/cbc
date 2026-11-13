package ke.ac.bics.cbcapp.data.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface OnboardingApi {
    @GET("api/v1/profiles/{studentId}")
    suspend fun getProfile(@Path("studentId") studentId: String): StudentProfileDto

    @POST("api/v1/profiles")
    suspend fun createProfile(@Body request: ProfileCreateDto): StudentProfileDto

    @GET("api/v1/intro-quiz")
    suspend fun getIntroQuiz(): IntroQuizDto

    @POST("api/v1/profiles/{studentId}/placement")
    suspend fun submitPlacement(
        @Path("studentId") studentId: String,
        @Body request: PlacementSubmissionDto
    ): PlacementResponseDto
}
