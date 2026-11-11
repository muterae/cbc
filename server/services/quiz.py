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
    # Optional only for tests/admin tooling. The live path reads the band from
    # the stored learner profile.
    competency_band: str | None = None


class QuizQuestion(QuizItem):
    question_number: int = Field(ge=1)
    pedagogical_objective: str = Field(min_length=1)


class QuizResponse(BaseModel):
    strand: str
    competency_band: str
    questions: list[QuizQuestion]
    teacher_insight_summary: str
