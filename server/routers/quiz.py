"""Adaptive quiz endpoint."""

from fastapi import APIRouter, HTTPException

from retriever import retrieve_lessons
from services.band_playbook import get_playbook
from services.curriculum import resolve_location
from services.generative_ai import generate_quiz
from services.quiz import AdaptiveQuizRequest, QuizResponse

router = APIRouter(prefix="/api/v1", tags=["quiz"])


@router.post("/adaptive-quiz", response_model=QuizResponse)
def adaptive_quiz(request: AdaptiveQuizRequest) -> QuizResponse:
    """Generate a band-appropriate quiz grounded in the KICD corpus."""
    try:
        location = resolve_location(request.strand, request.sub_strand)
        playbook = get_playbook(request.competency_band)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    lessons = retrieve_lessons(
        location.strand,
        location.sub_strand,
        playbook.code.value,
    )
    return generate_quiz(request, location, playbook, lessons)
