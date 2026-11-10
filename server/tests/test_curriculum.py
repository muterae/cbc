import pytest

from services.curriculum import resolve_location


def test_resolve_top_level_strand():
    location = resolve_location("NUMBERS")

    assert location.strand == "NUMBERS"
    assert location.sub_strand is None
    assert location.display == "Numbers"


def test_resolve_sub_strand_alone():
    location = resolve_location("Addition")

    assert location.strand == "NUMBERS"
    assert location.sub_strand == "ADDITION"
    assert location.display == "Numbers - Addition"


def test_resolve_combined_display_name():
    location = resolve_location("Numbers - Addition")

    assert location.strand == "NUMBERS"
    assert location.sub_strand == "ADDITION"


def test_resolve_explicit_sub_strand():
    location = resolve_location("GEOMETRY", "Position and Direction")

    assert location.strand == "GEOMETRY"
    assert location.sub_strand == "POSITION AND DIRECTION"
    assert location.display == "Geometry - Position and Direction"


def test_mathematics_means_no_strand_filter():
    assert resolve_location("Mathematics").strand is None
    assert resolve_location("math").display == "Mathematics"


def test_invalid_strand_raises():
    with pytest.raises(ValueError):
        resolve_location("Geography")


def test_sub_strand_must_belong_to_strand():
    with pytest.raises(ValueError):
        resolve_location("GEOMETRY", "MONEY")


def test_conflicting_strand_and_sub_strand_raises():
    with pytest.raises(ValueError):
        resolve_location("Numbers - Addition", "Subtraction")
