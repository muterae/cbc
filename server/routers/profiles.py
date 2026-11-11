"""Profile creation, lookup and placement submission."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.band_playbook import Band, get_playbook
from services.intro_quiz import get_intro_quiz
from services.profile_store import (
    InMemoryProfileStore,
    StudentProfile,
    get_profile_store,
    provisional_band,
)

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


class ProfileCreate(BaseModel):
    student_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    grade: str = "Grade 3"
    class_name: str = "3A"
    term: str = "Term 1"


class PlacementAnswer(BaseModel):
    question_number: int = Field(ge=1)
    selected_option: str = Field(min_length=1)


class PlacementSubmission(BaseModel):
    quiz_id: str = Field(min_length=1)
    answers: list[PlacementAnswer]


class PlacementResult(BaseModel):
    quiz_id: str
    correct: int
    total: int
    per_band: dict[str, int]
    band: str
    band_status: str
    teacher_insight_summary: str


class PlacementResponse(BaseModel):
    profile: StudentProfile
    result: PlacementResult


def _result_from_profile(profile: StudentProfile, quiz_id: str, total: int) -> PlacementResult:
    band = profile.competency_band or Band.BE.value
    return PlacementResult(
        quiz_id=profile.placement_quiz_id or quiz_id,
        correct=profile.placement_score or 0,
        total=profile.placement_total or total,
        per_band=profile.placement_per_band,
        band=band,
        band_status=profile.band_status,
        teacher_insight_summary=get_playbook(band).teacher_insight_template,
    )


@router.post("", response_model=StudentProfile)
def upsert_profile(
    payload: ProfileCreate,
    store: InMemoryProfileStore = Depends(get_profile_store),
) -> StudentProfile:
    """Create a profile or return the existing one with updated basics."""
    return store.upsert(
        student_id=payload.student_id,
        name=payload.name,
        grade=payload.grade,
        class_name=payload.class_name,
        term=payload.term,
    )


@router.get("/{student_id}", response_model=StudentProfile)
def read_profile(
    student_id: str,
    store: InMemoryProfileStore = Depends(get_profile_store),
) -> StudentProfile:
    profile = store.get(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


@router.post("/{student_id}/placement", response_model=PlacementResponse)
def submit_placement(
    student_id: str,
    payload: PlacementSubmission,
    store: InMemoryProfileStore = Depends(get_profile_store),
) -> PlacementResponse:
    """Score the fixed baseline quiz and store the provisional band."""
    profile = store.get(student_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    quiz = get_intro_quiz()
    if payload.quiz_id != quiz.quiz_id:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Quiz version '{payload.quiz_id}' is not the active version "
                f"'{quiz.quiz_id}'. Refresh the quiz."
            ),
        )

    if profile.placement_completed:
        if profile.placement_quiz_id != quiz.quiz_id:
            raise HTTPException(
                status_code=409,
                detail="Placement already completed with a different quiz version.",
            )
        return PlacementResponse(
            profile=profile,
            result=_result_from_profile(profile, quiz.quiz_id, len(quiz.questions)),
        )

    by_number = {question.question_number: question for question in quiz.questions}
    if len(payload.answers) != len(by_number):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(by_number)} answers, got {len(payload.answers)}.",
        )

    seen: set[int] = set()
    correct = 0
    per_band = {band.name: 0 for band in Band}

    for answer in payload.answers:
        if answer.question_number in seen:
            raise HTTPException(
                status_code=400,
                detail=f"Duplicate answer for question {answer.question_number}.",
            )
        seen.add(answer.question_number)

        question = by_number.get(answer.question_number)
        if question is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown question number {answer.question_number}.",
            )
        if answer.selected_option not in question.options:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Option for question {answer.question_number} is not one "
                    "of the available options."
                ),
            )
        if answer.selected_option == question.correct_answer:
            correct += 1
            per_band[question.band.name] += 1

    if seen != set(by_number):
        raise HTTPException(status_code=400, detail="Every question must be answered.")

    band = provisional_band(per_band)
    try:
        updated = store.save_placement(
            student_id=student_id,
            quiz_id=quiz.quiz_id,
            correct=correct,
            total=len(by_number),
            per_band=per_band,
            band=band,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return PlacementResponse(
        profile=updated,
        result=PlacementResult(
            quiz_id=quiz.quiz_id,
            correct=correct,
            total=len(by_number),
            per_band=per_band,
            band=band.value,
            band_status=updated.band_status,
            teacher_insight_summary=get_playbook(band).teacher_insight_template,
        ),
    )
