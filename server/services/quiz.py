"""Request and response models for the adaptive quiz endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from services.band_playbook import QuizItem


class AdaptiveQuizRequest(BaseModel):
    student_id: str = Field(min_length=1)
    strand: str = "Mathematics"
    sub_strand: str | None = None
    session_type: Literal["placement", "practice", "assessment"] = "practice"
    # Temporary until learner profiles and the predictor are wired in. The
    # stored profile will supply this in the live onboarding flow.
    competency_band: str = "Meeting Expectation"


class QuizQuestion(QuizItem):
    question_number: int = Field(ge=1)
    pedagogical_objective: str = Field(min_length=1)


class QuizResponse(BaseModel):
    strand: str
    competency_band: str
    questions: list[QuizQuestion]
    teacher_insight_summary: str
