import pytest
from pydantic import ValidationError

from services.band_playbook import (
    BAND_PLAYBOOK,
    Band,
    DOCS_PATH,
    QuizItem,
    get_playbook,
    list_playbooks,
    render_markdown,
    resolve_band,
    validate_item,
    validate_quiz,
)


def test_all_bands_present_and_ranked():
    assert set(BAND_PLAYBOOK) == set(Band)
    assert [playbook.rank for playbook in list_playbooks()] == [1, 2, 3, 4]


def test_question_counts():
    assert {band: BAND_PLAYBOOK[band].question_count for band in Band} == {
        Band.BE: 4,
        Band.AE: 5,
        Band.ME: 5,
        Band.EE: 6,
    }


def test_number_range_and_regrouping_ladder():
    assert BAND_PLAYBOOK[Band.BE].number_range == (0, 10)
    assert BAND_PLAYBOOK[Band.AE].number_range == (0, 20)
    assert BAND_PLAYBOOK[Band.ME].number_range == (0, 100)
    assert BAND_PLAYBOOK[Band.EE].number_range == (0, 100)

    assert BAND_PLAYBOOK[Band.BE].regrouping is False
    assert BAND_PLAYBOOK[Band.AE].regrouping is False
    assert BAND_PLAYBOOK[Band.ME].regrouping is True
    assert BAND_PLAYBOOK[Band.EE].regrouping is True


def test_word_caps_and_steps_increase():
    word_caps = [BAND_PLAYBOOK[band].max_question_words for band in Band]
    steps = [BAND_PLAYBOOK[band].max_steps for band in Band]

    assert word_caps == [12, 20, 30, 40]
    assert steps == [1, 1, 2, 3]


def test_every_band_has_guidance_and_a_valid_example():
    for playbook in list_playbooks():
        assert playbook.prompt_directives
        assert playbook.forbidden
        assert playbook.teacher_insight_template
        assert playbook.description

        item = playbook.example_item
        assert len(item.options) == 4
        assert len(set(item.options)) == 4
        assert item.correct_answer in item.options
        assert validate_item(item, playbook) == []


def test_resolve_band_accepts_code_name_and_slug():
    assert resolve_band("BE") is Band.BE
    assert resolve_band("be") is Band.BE
    assert resolve_band("Below Expectation") is Band.BE
    assert resolve_band("below-expectation") is Band.BE
    assert resolve_band("MEETING EXPECTATION") is Band.ME

    with pytest.raises(ValueError):
        resolve_band("unknown")


def test_get_playbook_returns_expected_band():
    assert get_playbook("ee").code is Band.EE


def test_quiz_item_rejects_duplicate_options():
    with pytest.raises(ValidationError):
        QuizItem(
            question_text="How many?",
            options=["A) 1", "A) 1", "C) 2", "D) 3"],
            correct_answer="A) 1",
            hint="Count them.",
        )


def test_quiz_item_rejects_answer_outside_options():
    with pytest.raises(ValidationError):
        QuizItem(
            question_text="How many?",
            options=["A) 1", "B) 2", "C) 3", "D) 4"],
            correct_answer="E) 5",
            hint="Count them.",
        )


def test_validate_item_catches_word_limit_and_option_format():
    item = QuizItem(
        question_text=" ".join(["word"] * 13),
        options=["1", "2", "3", "4"],
        correct_answer="1",
        hint="Count them.",
    )
    errors = validate_item(item, Band.BE)

    assert any("exceeds" in error for error in errors)
    assert any("A) ..." in error for error in errors)


def test_validate_quiz_checks_count_and_items():
    item = BAND_PLAYBOOK[Band.BE].example_item
    errors = validate_quiz([item], Band.BE)

    assert any("expected 4 questions" in error for error in errors)


def test_markdown_companion_is_in_sync():
    assert DOCS_PATH.exists()
    assert DOCS_PATH.read_text(encoding="utf-8") == render_markdown()
