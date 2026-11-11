"""Adaptive quiz endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from retriever import retrieve_lessons
from services.band_playbook import get_playbook
from services.curriculum import resolve_location
from services.generative_ai import generate_quiz
from services.profile_store import InMemoryProfileStore, get_profile_store
from services.quiz import AdaptiveQuizRequest, QuizResponse

router = APIRouter(prefix="/api/v1", tags=["quiz"])


@router.post("/adaptive-quiz", response_model=QuizResponse)
def adaptive_quiz(
    request: AdaptiveQuizRequest,
    store: InMemoryProfileStore = Depends(get_profile_store),
) -> QuizResponse:
    """Generate a band-appropriate quiz grounded in the KICD corpus."""
    band = request.competency_band
    if band is None:
        profile = store.get(request.student_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found.")
        if profile.competency_band is None:
            raise HTTPException(
                status_code=409,
                detail="Placement has not been completed for this learner.",
            )
        band = profile.competency_band

    try:
        location = resolve_location(request.strand, request.sub_strand)
        playbook = get_playbook(band)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    lessons = retrieve_lessons(
        location.strand,
        location.sub_strand,
        playbook.code.value,
    )
    return generate_quiz(request, location, playbook, lessons)
