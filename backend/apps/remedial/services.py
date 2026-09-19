import json
import logging

import requests
from django.conf import settings
from django.utils import timezone

from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp

from .models import LOW_SCORE_THRESHOLD, RemedialSession

logger = logging.getLogger(__name__)

REMEDIAL_QUESTION_COUNT = 6
MAX_REMEDIAL_XP = 20

_GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def maybe_start_remedial_session(attempt) -> RemedialSession | None:
    """Called right after a `Test` is graded — a low score quietly opens an
    AI-assisted practice session for that attempt (idempotent: repeated calls
    for the same attempt reuse the existing session instead of spawning more).
    """
    if attempt.score_percent is None or attempt.score_percent >= LOW_SCORE_THRESHOLD:
        return None

    session, _created = RemedialSession.objects.get_or_create(
        attempt=attempt,
        defaults={"student": attempt.student, "subject": attempt.test.subject},
    )
    return session


def _call_gemini(*, prompt: str, json_mode: bool = False) -> str | None:
    """Plain synchronous call to the Gemini `generateContent` API. Never
    raises — logs and returns None on any failure, the same "fail quiet"
    contract as `apps.telegram_bot.services.send_telegram_message`.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set — cannot call Gemini.")
        return None

    generation_config = {"temperature": 0.7}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    url = _GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL)

    try:
        response = requests.post(
            url,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.RequestException:
        logger.warning("Gemini request failed.")
        return None
    except (KeyError, IndexError, ValueError):
        logger.warning("Unexpected Gemini response shape.")
        return None


def generate_explanation(session: RemedialSession) -> str | None:
    """Idempotent — a session only ever gets one explanation."""
    if session.explanation:
        return session.explanation

    wrong_question_texts = [
        answer.question.text
        for answer in session.attempt.answers.select_related("question", "selected_option")
        if not answer.selected_option.is_correct
    ]
    prompt = (
        f'Sen mehribon va sabrli o\'qituvchisan. O\'quvchi "{session.subject.name}" fanidan test topshirdi '
        f"va {session.attempt.score_percent:.0f}% ball oldi — bu past natija.\n"
        "U quyidagi savollarda xato qildi:\n"
        + "\n".join(f"- {text}" for text in wrong_question_texts[:10])
        + "\n\nShu mavzuni O'ZBEK TILIDA, oddiy va tushunarli qilib, 4-6 jumlada tushuntir. "
        "Murakkab atamalardan qoching, kerak bo'lsa oddiy misol keltiring, iliq va rag'batlantiruvchi "
        "ohangda yozing. Faqat tushuntirish matnini yoz, boshqa hech narsa qo'shma."
    )

    content = _call_gemini(prompt=prompt)
    if content is None:
        return None

    session.explanation = content.strip()
    session.status = RemedialSession.Status.EXPLAINED
    session.save(update_fields=["explanation", "status", "updated_at"])
    return session.explanation


def generate_game_questions(session: RemedialSession) -> list[dict] | None:
    """Idempotent — a session only ever gets one AI-generated question set,
    stored as a JSON snapshot (see `RemedialSession.questions`).
    """
    if session.questions:
        return session.questions

    prompt = (
        f'"{session.subject.name}" fanidan, quyidagi tushuntirishga asoslanib, o\'quvchi uchun '
        f"{REMEDIAL_QUESTION_COUNT} ta ODDIY va QISQA ko'p variantli mashq savoli tuzib ber (arqon tortish "
        "o'yini uchun — tezkor va oson bo'lsin, avvalgi testdagi savollarni takrorlama).\n\n"
        f"Tushuntirish: {session.explanation}\n\n"
        "Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        '{"questions": [{"text": "...", "options": ["...", "...", "...", "..."], "correct_index": 0}]}\n'
        "Har savolda aniq 4 ta variant va faqat bitta to'g'ri javob bo'lsin (correct_index — 0 dan boshlab). "
        "Hammasi o'zbek tilida bo'lsin."
    )

    content = _call_gemini(prompt=prompt, json_mode=True)
    if content is None:
        return None

    try:
        questions = json.loads(content)["questions"]
        if not isinstance(questions, list) or not questions:
            raise ValueError
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.warning("Could not parse Gemini question JSON for remedial session %s", session.pk)
        return None

    session.questions = questions
    session.save(update_fields=["questions", "updated_at"])
    return questions


def submit_game(*, session: RemedialSession, answers: dict[int, int]) -> RemedialSession:
    """`answers` is {question_index: selected_option_index}."""
    if session.status == RemedialSession.Status.COMPLETED:
        raise ValueError("Bu mashq allaqachon yakunlangan.")
    if not session.questions:
        raise ValueError("Savollar hali tayyor emas.")

    total = len(session.questions)
    correct = sum(
        1
        for index, question in enumerate(session.questions)
        if answers.get(index) == question.get("correct_index")
    )
    score_percent = round((correct / total) * 100, 2) if total else 0.0
    xp_awarded = round(MAX_REMEDIAL_XP * score_percent / 100)

    session.score_percent = score_percent
    session.xp_awarded = xp_awarded
    session.status = RemedialSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.save(
        update_fields=["score_percent", "xp_awarded", "status", "completed_at", "updated_at"]
    )

    if xp_awarded > 0:
        award_xp(
            student=session.student,
            amount=xp_awarded,
            source=XPTransaction.Source.REMEDIAL_GAME,
            related_object=session,
            reason=f"{session.subject.name} — mashq o'yini",
        )

    return session
