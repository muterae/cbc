"""Static baseline quiz endpoint."""

from fastapi import APIRouter, Response

from services.intro_quiz import (
    IntroQuizResponse,
    get_intro_quiz,
    to_response,
)

router = APIRouter(prefix="/api/v1", tags=["intro-quiz"])


@router.get("/intro-quiz", response_model=IntroQuizResponse)
def intro_quiz(response: Response) -> IntroQuizResponse:
    """Return the same 12-item baseline quiz for every learner."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    return to_response(get_intro_quiz())
