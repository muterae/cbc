"""In-memory learner profiles for the simulation build.

The store is process-local and intentionally not a database. It is wrapped in a
small interface so a SQLite/Postgres implementation can replace it later without
changing the routers or the mobile contract.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from services.band_playbook import Band


class StudentProfile(BaseModel):
    student_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    grade: str = "Grade 3"
    class_name: str = "3A"
    term: str = "Term 1"

    competency_band: str | None = None
    band_status: Literal["provisional", "confirmed"] = "provisional"
    band_source: Literal["placement", "predictor", "teacher", "none"] = "none"
    placement_completed: bool = False
    placement_quiz_id: str | None = None
    placement_score: int | None = None
    placement_total: int | None = None
    placement_per_band: dict[str, int] = Field(default_factory=dict)

    xp: int = 0
    streak_days: int = 0
    daily_goal: int = 5

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProfileStore(Protocol):
    def get(self, student_id: str) -> StudentProfile | None: ...

    def upsert(
        self,
        student_id: str,
        name: str,
        grade: str = "Grade 3",
        class_name: str = "3A",
        term: str = "Term 1",
    ) -> StudentProfile: ...

    def save_placement(
        self,
        student_id: str,
        quiz_id: str,
        correct: int,
        total: int,
        per_band: dict[str, int],
        band: Band,
    ) -> StudentProfile: ...


def provisional_band(per_band: dict[str, int]) -> Band:
    """Highest band with at least two correct items; BE otherwise."""
    for band in reversed(list(Band)):
        if per_band.get(band.name, 0) >= 2:
            return band
    return Band.BE


class InMemoryProfileStore:
    def __init__(self, seed: bool = True) -> None:
        self._lock = threading.RLock()
        self._profiles: dict[str, StudentProfile] = {}
        if seed:
            self._seed_demo_profiles()

    def _seed_demo_profiles(self) -> None:
        self._profiles["std_ke_09823"] = StudentProfile(
            student_id="std_ke_09823",
            name="Amina",
            class_name="3A",
            competency_band=Band.AE.value,
            band_status="provisional",
            band_source="placement",
            placement_completed=True,
            placement_quiz_id="intro-v1",
            placement_score=7,
            placement_total=12,
            placement_per_band={"BE": 3, "AE": 2, "ME": 1, "EE": 1},
            xp=280,
            streak_days=4,
        )
        self._profiles["std_ke_09824"] = StudentProfile(
            student_id="std_ke_09824",
            name="Brian",
            class_name="3A",
            competency_band=Band.ME.value,
            band_status="provisional",
            band_source="placement",
            placement_completed=True,
            placement_quiz_id="intro-v1",
            placement_score=9,
            placement_total=12,
            placement_per_band={"BE": 3, "AE": 3, "ME": 2, "EE": 1},
            xp=320,
            streak_days=6,
        )

    def get(self, student_id: str) -> StudentProfile | None:
        with self._lock:
            return self._profiles.get(student_id)

    def upsert(
        self,
        student_id: str,
        name: str,
        grade: str = "Grade 3",
        class_name: str = "3A",
        term: str = "Term 1",
    ) -> StudentProfile:
        now = datetime.now(timezone.utc)
        with self._lock:
            existing = self._profiles.get(student_id)
            if existing is None:
                profile = StudentProfile(
                    student_id=student_id,
                    name=name,
                    grade=grade,
                    class_name=class_name,
                    term=term,
                    created_at=now,
                    updated_at=now,
                )
            else:
                profile = existing.model_copy(
                    update={
                        "name": name,
                        "grade": grade,
                        "class_name": class_name,
                        "term": term,
                        "updated_at": now,
                    }
                )
            self._profiles[student_id] = profile
            return profile

    def save_placement(
        self,
        student_id: str,
        quiz_id: str,
        correct: int,
        total: int,
        per_band: dict[str, int],
        band: Band,
    ) -> StudentProfile:
        now = datetime.now(timezone.utc)
        with self._lock:
            profile = self._profiles.get(student_id)
            if profile is None:
                raise KeyError(student_id)
            if profile.placement_completed:
                if profile.placement_quiz_id != quiz_id:
                    raise ValueError(
                        "placement already completed with a different quiz version"
                    )
                return profile

            updated = profile.model_copy(
                update={
                    "competency_band": band.value,
                    "band_status": "provisional",
                    "band_source": "placement",
                    "placement_completed": True,
                    "placement_quiz_id": quiz_id,
                    "placement_score": correct,
                    "placement_total": total,
                    "placement_per_band": dict(per_band),
                    "updated_at": now,
                }
            )
            self._profiles[student_id] = updated
            return updated


_store_lock = threading.Lock()
_store: InMemoryProfileStore | None = None


def get_profile_store() -> InMemoryProfileStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = InMemoryProfileStore()
    return _store


def reset_profile_store() -> InMemoryProfileStore:
    global _store
    with _store_lock:
        _store = InMemoryProfileStore()
    return _store
