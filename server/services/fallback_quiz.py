"""Deterministic fallback quizzes used when the LLM fails validation.

The bank is deliberately small and generic. It keeps practice running when Groq
is unavailable or returns unusable JSON; it is not a substitute for the
curriculum-grounded generated quiz.
"""

from __future__ import annotations

from services.band_playbook import Band, BandPlaybook
from services.quiz import QuizQuestion

_BANK: dict[Band, list[dict]] = {
    Band.BE: [
        {
            "question_text": "There are 4 mangoes. How many mangoes are there?",
            "options": ["A) 2", "B) 3", "C) 4", "D) 5"],
            "correct_answer": "C) 4",
            "hint": "Touch each mango as you count: one, two, three, four.",
        },
        {
            "question_text": "Count the sticks: | | |. How many sticks are there?",
            "options": ["A) 2", "B) 3", "C) 4", "D) 5"],
            "correct_answer": "B) 3",
            "hint": "Point to each stick as you count.",
        },
        {
            "question_text": "Which number comes after 5?",
            "options": ["A) 3", "B) 4", "C) 6", "D) 7"],
            "correct_answer": "C) 6",
            "hint": "Count forward from 5.",
        },
        {
            "question_text": "Which group has 2 bottle tops?",
            "options": [
                "A) 1 bottle top",
                "B) 2 bottle tops",
                "C) 3 bottle tops",
                "D) 4 bottle tops",
            ],
            "correct_answer": "B) 2 bottle tops",
            "hint": "Count the bottle tops in each group.",
        },
    ],
    Band.AE: [
        {
            "question_text": (
                "Amina has 12 mangoes. She buys 5 more. "
                "How many mangoes does she have now?"
            ),
            "options": ["A) 15", "B) 16", "C) 17", "D) 18"],
            "correct_answer": "C) 17",
            "hint": "Start at 12 and count 5 steps forward.",
        },
        {
            "question_text": (
                "Juma has 9 sweets. He buys 6 more. How many sweets does he have?"
            ),
            "options": ["A) 13", "B) 14", "C) 15", "D) 16"],
            "correct_answer": "C) 15",
            "hint": "Start at 9 and count 6 steps forward.",
        },
        {
            "question_text": (
                "There are 18 goats. 4 goats go away. How many goats remain?"
            ),
            "options": ["A) 12", "B) 13", "C) 14", "D) 15"],
            "correct_answer": "C) 14",
            "hint": "Start at 18 and count 4 steps backward.",
        },
        {
            "question_text": (
                "A pencil costs 5 shillings. How much do 2 pencils cost?"
            ),
            "options": ["A) 5", "B) 10", "C) 15", "D) 20"],
            "correct_answer": "B) 10",
            "hint": "Add 5 two times.",
        },
        {
            "question_text": "Which shape has 3 sides?",
            "options": ["A) Circle", "B) Triangle", "C) Square", "D) Rectangle"],
            "correct_answer": "B) Triangle",
            "hint": "Tri means three.",
        },
    ],
    Band.ME: [
        {
            "question_text": "A pencil costs 5 shillings. How much do 4 pencils cost?",
            "options": ["A) 9", "B) 15", "C) 20", "D) 25"],
            "correct_answer": "C) 20",
            "hint": "Multiply the cost of one pencil by the number of pencils.",
        },
        {
            "question_text": (
                "There are 36 boys and 27 girls in a hall. "
                "How many children are there?"
            ),
            "options": ["A) 53", "B) 61", "C) 63", "D) 73"],
            "correct_answer": "C) 63",
            "hint": "Add the boys and the girls.",
        },
        {
            "question_text": (
                "A farmer has 52 eggs. He sells 18. How many eggs remain?"
            ),
            "options": ["A) 30", "B) 32", "C) 34", "D) 44"],
            "correct_answer": "C) 34",
            "hint": "Take away 18 from 52.",
        },
        {
            "question_text": "What is one half of 10 mangoes?",
            "options": ["A) 2", "B) 4", "C) 5", "D) 10"],
            "correct_answer": "C) 5",
            "hint": "Share 10 into two equal groups.",
        },
        {
            "question_text": (
                "A book costs 65 shillings. You pay 100 shillings. "
                "How much change do you get?"
            ),
            "options": ["A) 25", "B) 35", "C) 45", "D) 55"],
            "correct_answer": "B) 35",
            "hint": "Subtract 65 from 100.",
        },
    ],
    Band.EE: [
        {
            "question_text": "What number goes in the box? \u25a1 + 6 = 15",
            "options": ["A) 7", "B) 8", "C) 9", "D) 10"],
            "correct_answer": "C) 9",
            "hint": "Work backwards: subtract 6 from 15.",
        },
        {
            "question_text": "What number goes in the box? 7 \u00d7 \u25a1 = 28",
            "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
            "correct_answer": "B) 4",
            "hint": "Share 28 into 7 equal groups.",
        },
        {
            "question_text": "What number goes in the box? 45 + \u25a1 = 72",
            "options": ["A) 17", "B) 27", "C) 37", "D) 47"],
            "correct_answer": "B) 27",
            "hint": "Subtract 45 from 72.",
        },
        {
            "question_text": "Which fraction is greater: one half or one quarter?",
            "options": [
                "A) One quarter",
                "B) One half",
                "C) They are equal",
                "D) Cannot tell",
            ],
            "correct_answer": "B) One half",
            "hint": "One half is larger than one quarter.",
        },
        {
            "question_text": (
                "A shirt costs 65 shillings and a cap costs 20 shillings. "
                "You pay 100 shillings. How much change do you get?"
            ),
            "options": ["A) 5", "B) 15", "C) 25", "D) 35"],
            "correct_answer": "B) 15",
            "hint": "Find the total cost first, then subtract it from 100.",
        },
        {
            "question_text": "What sign goes in the box? 6 \u25a1 3 = 18",
            "options": ["A) +", "B) \u2212", "C) \u00d7", "D) \u00f7"],
            "correct_answer": "C) \u00d7",
            "hint": "Test each sign until the answer is 18.",
        },
    ],
}


def build_fallback_quiz(playbook: BandPlaybook) -> list[QuizQuestion]:
    """Return the deterministic bank for the band, trimmed to its item count."""
    items = _BANK[playbook.code][: playbook.question_count]
    return [
        QuizQuestion(
            question_number=number,
            question_text=item["question_text"],
            options=item["options"],
            correct_answer=item["correct_answer"],
            hint=item["hint"],
            pedagogical_objective=playbook.task_style,
        )
        for number, item in enumerate(items, start=1)
    ]
