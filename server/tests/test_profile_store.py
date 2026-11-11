import pytest

from services.band_playbook import Band
from services.profile_store import (
    InMemoryProfileStore,
    provisional_band,
)


def test_upsert_is_idempotent_and_preserves_created_at():
    store = InMemoryProfileStore(seed=False)

    first = store.upsert("std_001", "Amina")
    second = store.upsert("std_001", "Amina W.")

    assert second.name == "Amina W."
    assert second.created_at == first.created_at
    assert store.get("std_001") == second


def test_save_placement_sets_provisional_band():
    store = InMemoryProfileStore(seed=False)
    store.upsert("std_001", "Amina")

    updated = store.save_placement(
        student_id="std_001",
        quiz_id="intro-v1",
        correct=7,
        total=12,
        per_band={"BE": 3, "AE": 2, "ME": 1, "EE": 1},
        band=Band.AE,
    )

    assert updated.competency_band == Band.AE.value
    assert updated.band_status == "provisional"
    assert updated.band_source == "placement"
    assert updated.placement_completed is True
    assert updated.placement_score == 7


def test_conflicting_placement_version_is_rejected():
    store = InMemoryProfileStore(seed=False)
    store.upsert("std_001", "Amina")
    store.save_placement(
        "std_001", "intro-v1", 7, 12, {"BE": 3, "AE": 2, "ME": 1, "EE": 1}, Band.AE
    )

    with pytest.raises(ValueError):
        store.save_placement(
            "std_001", "intro-v2", 8, 12, {"BE": 3, "AE": 3, "ME": 1, "EE": 1}, Band.AE
        )


def test_provisional_band_rule():
    assert provisional_band({"BE": 3, "AE": 2, "ME": 1, "EE": 0}) == Band.AE
    assert provisional_band({"BE": 1, "AE": 1, "ME": 1, "EE": 0}) == Band.BE
    assert provisional_band({"BE": 3, "AE": 3, "ME": 2, "EE": 1}) == Band.ME


def test_seeded_demo_profile():
    store = InMemoryProfileStore()
    profile = store.get("std_ke_09823")

    assert profile is not None
    assert profile.name == "Amina"
    assert profile.placement_completed is True
