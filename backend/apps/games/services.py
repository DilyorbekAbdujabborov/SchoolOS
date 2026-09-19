import json
import logging

from django.utils import timezone

from apps.common.gemini import call_gemini
from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp

from .models import GameSession

logger = logging.getLogger(__name__)

GAME_QUESTION_COUNT = 8
MAX_GAME_XP = 25

_GAME_LABELS = {
    GameSession.GameType.TUG_OF_WAR: "arqon tortish",
    GameSession.GameType.QUIZ: "viktorina",
}


def start_game(*, student, subject, game_type: str) -> GameSession:
    return GameSession.objects.create(student=student, subject=subject, game_type=game_type)


def generate_questions(session: GameSession) -> list[dict] | None:
    """Idempotent — a session only ever gets one AI-generated question set."""
    if session.questions:
        return session.questions

    class_name = session.student.school_class.name if session.student.school_class_id else "o'rta"
    game_label = _GAME_LABELS.get(session.game_type, "mashq")
    prompt = (
        f'"{session.subject.name}" fanidan, {class_name} sinf darajasida {GAME_QUESTION_COUNT} ta '
        f"ODDIY va QISQA ko'p variantli {game_label} savoli tuzib ber. Turli mavzu va qiyinlik darajasidan "
        "bo'lsin.\n\n"
        "Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        '{"questions": [{"text": "...", "options": ["...", "...", "...", "..."], "correct_index": 0}]}\n'
        "Har savolda aniq 4 ta variant va faqat bitta to'g'ri javob bo'lsin (correct_index — 0 dan boshlab). "
        "Hammasi o'zbek tilida bo'lsin."
    )

    content = call_gemini(prompt=prompt, json_mode=True)
    if content is None:
        return None

    try:
        questions = json.loads(content)["questions"]
        if not isinstance(questions, list) or not questions:
            raise ValueError
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.warning("Could not parse Gemini question JSON for game session %s", session.pk)
        return None

    session.questions = questions[:GAME_QUESTION_COUNT]
    session.save(update_fields=["questions", "updated_at"])
    return session.questions


def submit_game(*, session: GameSession, answers: dict[int, int]) -> GameSession:
    """`answers` is {question_index: selected_option_index}."""
    if session.status == GameSession.Status.COMPLETED:
        raise ValueError("Bu o'yin allaqachon yakunlangan.")
    if not session.questions:
        raise ValueError("Savollar hali tayyor emas.")

    total = len(session.questions)
    correct = sum(
        1
        for index, question in enumerate(session.questions)
        if answers.get(index) == question.get("correct_index")
    )
    score_percent = round((correct / total) * 100, 2) if total else 0.0
    xp_awarded = round(MAX_GAME_XP * score_percent / 100)

    session.score_percent = score_percent
    session.xp_awarded = xp_awarded
    session.status = GameSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.save(
        update_fields=["score_percent", "xp_awarded", "status", "completed_at", "updated_at"]
    )

    if xp_awarded > 0:
        game_label = _GAME_LABELS.get(session.game_type, "o'yin")
        award_xp(
            student=session.student,
            amount=xp_awarded,
            source=XPTransaction.Source.GAME,
            related_object=session,
            reason=f"{session.subject.name} — {game_label}",
        )

    return session
