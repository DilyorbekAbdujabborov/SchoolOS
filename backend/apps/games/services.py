import json
import logging

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.academics.models import Subject
from apps.common.gemini import call_gemini
from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp
from apps.schools.models import SchoolClass

from .models import GameSession, PooledQuestion, PooledQuestionServed

logger = logging.getLogger(__name__)

GAME_QUESTION_COUNT = 8
MAX_GAME_XP = 25

# A pool this low triggers `tasks.refill_low_pools`; one refill call asks Gemini
# for this many new questions at once. Both are pool-wide, not per-student —
# see `refill_pool`.
POOL_LOW_THRESHOLD = 20
POOL_REFILL_BATCH = 30

_GAME_LABELS = {
    GameSession.GameType.TUG_OF_WAR: "arqon tortish",
    GameSession.GameType.QUIZ: "viktorina",
}


def start_game(*, student, subject, game_type: str) -> GameSession:
    return GameSession.objects.create(student=student, subject=subject, game_type=game_type)


def pick_session_questions(session: GameSession) -> list[dict] | None:
    """Pool-backed replacement for a live per-session Gemini call — draws
    `GAME_QUESTION_COUNT` questions from the (subject, school_class) pool that
    `refill_pool` keeps stocked, instead of ever calling Gemini during play.

    Idempotent per session, same contract as before. Returns `None` when
    there's nowhere to draw from (student has no class, or the pool doesn't
    have enough questions yet) — the caller shows a "not ready" message rather
    than falling back to a live AI call, so a game start never risks the
    Gemini rate limit.

    `select_for_update` + a re-check under the lock guards against two
    near-simultaneous requests for the same session (a double-click, a
    duplicate tab) both picking their own question set — without it, both
    would mark their draw "served" via `PooledQuestionServed` before either
    save won, quietly burning pool capacity for a set of questions nobody
    ever actually played.
    """
    if session.questions:
        return session.questions

    with transaction.atomic():
        # A separate, lock-held copy — `session` (the caller's object) is kept
        # in sync below rather than rebound, since callers rely on it being
        # mutated in place (e.g. reading `session.questions` right after this
        # call without using the return value).
        locked = GameSession.objects.select_for_update().select_related("student", "subject").get(pk=session.pk)
        if locked.questions:
            session.questions = locked.questions
            return locked.questions

        student = locked.student
        if not student.school_class_id:
            return None

        pool = PooledQuestion.objects.filter(subject=locked.subject, school_class_id=student.school_class_id)

        served_ids = set(
            PooledQuestionServed.objects.filter(student=student, question__in=pool).values_list(
                "question_id", flat=True
            )
        )

        picked = list(pool.exclude(id__in=served_ids).order_by("?")[:GAME_QUESTION_COUNT])
        if len(picked) < GAME_QUESTION_COUNT:
            # Not enough fresh ones left for this student — top up with questions
            # they've already seen rather than come up short.
            still_needed = GAME_QUESTION_COUNT - len(picked)
            already_picked_ids = {q.id for q in picked}
            picked += list(
                pool.filter(id__in=served_ids).exclude(id__in=already_picked_ids).order_by("?")[:still_needed]
            )

        if len(picked) < GAME_QUESTION_COUNT:
            # The pool itself is too small overall — no amount of repeat-allowing helps.
            return None

        PooledQuestionServed.objects.bulk_create(
            (PooledQuestionServed(student=student, question=q) for q in picked),
            ignore_conflicts=True,
        )

        questions = [{"text": q.text, "options": q.options, "correct_index": q.correct_index} for q in picked]
        locked.questions = questions
        locked.save(update_fields=["questions", "updated_at"])
        session.questions = questions
        return questions


def refill_pool(*, subject: Subject, school_class: SchoolClass, batch_size: int = POOL_REFILL_BATCH) -> int:
    """The *only* place apps.games talks to Gemini — one batched call that
    tops up a subject+class pool. Called either by a director's manual
    "to'ldirish" action or by the scheduled `tasks.refill_low_pools`; never
    from a student's game-start request. Returns how many questions were
    actually added (0 if Gemini was unavailable or returned something unusable
    — same "fail quiet" contract as `call_gemini` itself).
    """
    game_label = "mashq"
    prompt = (
        f'"{subject.name}" fanidan, {school_class.name} sinf darajasida {batch_size} ta '
        f"ODDIY va QISQA ko'p variantli {game_label} savoli tuzib ber. Turli mavzu va qiyinlik darajasidan "
        "bo'lsin.\n\n"
        "Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        '{"questions": [{"text": "...", "options": ["...", "...", "...", "..."], "correct_index": 0}]}\n'
        "Har savolda aniq 4 ta variant va faqat bitta to'g'ri javob bo'lsin (correct_index — 0 dan boshlab). "
        "Hammasi o'zbek tilida bo'lsin."
    )

    content = call_gemini(prompt=prompt, json_mode=True)
    if content is None:
        return 0

    try:
        raw_questions = json.loads(content)["questions"]
        if not isinstance(raw_questions, list):
            raise ValueError
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.warning("Could not parse Gemini pool-refill JSON for %s / %s", subject, school_class)
        return 0

    valid = [
        q
        for q in raw_questions
        if isinstance(q, dict)
        and isinstance(q.get("text"), str)
        and q["text"]
        and isinstance(q.get("options"), list)
        and len(q["options"]) >= 2
        and isinstance(q.get("correct_index"), int)
        and 0 <= q["correct_index"] < len(q["options"])
    ]

    created = PooledQuestion.objects.bulk_create(
        PooledQuestion(
            subject=subject,
            school_class=school_class,
            text=q["text"],
            options=q["options"],
            correct_index=q["correct_index"],
        )
        for q in valid
    )
    return len(created)


def pool_status() -> list[dict]:
    """Every (subject, school_class) pool that has at least one question, with
    its current size — powers the director's pool-management page. A combo
    with zero questions simply doesn't appear here; a director bootstraps it
    with the manual refill action instead.
    """
    rows = (
        PooledQuestion.objects.values("subject", "subject__name", "school_class", "school_class__name")
        .annotate(count=Count("id"))
        .order_by("school_class__name", "subject__name")
    )
    return [
        {
            "subject": row["subject"],
            "subject_name": row["subject__name"],
            "school_class": row["school_class"],
            "school_class_name": row["school_class__name"],
            "count": row["count"],
        }
        for row in rows
    ]


def check_answer(*, session: GameSession, question_index: int, selected_index: int) -> bool:
    """Live per-question feedback for the tug-of-war rope — deliberately reveals only
    whether this one answer was right, never the full answer key.
    """
    if not session.questions or not (0 <= question_index < len(session.questions)):
        raise ValueError("Noto'g'ri savol raqami.")
    return session.questions[question_index].get("correct_index") == selected_index


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
