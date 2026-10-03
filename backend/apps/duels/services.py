import time
from datetime import timedelta

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.games import question_service
from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp
from apps.notifications.models import Notification
from apps.notifications.services import notify

from . import rules
from .models import Duel, DuelRating

K_FACTOR = 32
INVITE_TTL = timedelta(hours=24)
# How long past its last possible answer an unfinished match is left open.
STALE_MATCH_SLACK = timedelta(minutes=2)

OPEN_STATUSES = (Duel.Status.PENDING, Duel.Status.ACTIVE)


def display_name(student) -> str:
    """A student's name as other students see it — never their email."""
    return student.user.get_full_name() or student.user.username


def _now_ms() -> int:
    return int(time.time() * 1000)


def get_or_create_rating(student) -> DuelRating:
    org = getattr(student.user, "active_organization", None)
    if org is None:
        raise ValueError("Student has no active organization")
    org_id = getattr(student.user, "active_organization_id", None)
    rating, _created = DuelRating.objects.get_or_create(
        student=student,
        organization_id=org_id,
        defaults={"rating": DuelRating.DEFAULT_RATING}
    )
    return rating


# ---------- Creating / answering an invitation ----------


def _pick_questions(*, subject, student, count: int) -> list[dict]:
    """A duel's question set, drawn from the same shared bank every game uses
    (`apps.games.question_service`) — a duel is just another presentation of the
    selected subject's questions, so both players are always answered on the
    subject the challenger picked, from one question bank rather than a
    duel-only copy of it.

    If the subject has no questions at all that's a real empty state (the duel
    can't start); if it has fewer than asked for, the duel simply runs with
    what the bank has rather than refusing to start.
    """
    try:
        return question_service.get_questions(subject=subject, amount=count, student=student)
    except question_service.NoQuestionsAvailable as exc:
        raise ValueError(
            f"'{getattr(subject, 'name', subject)}' fani uchun savollar hali kiritilmagan. "
            "Avval bu fandan savollar qo'shing."
        ) from exc


@transaction.atomic
def create_duel(
    *,
    challenger,
    subject,
    question_count: int,
    difficulty: str = Duel.Difficulty.MEDIUM,
    opponent=None,
    ai_level: str = "",
    rematch_of: Duel | None = None,
) -> Duel:
    """An AI duel starts right away; a classmate duel is an invitation the
    opponent must accept. The configuration (subject, difficulty, question
    count) and the question set are fixed here and never change after."""
    if not challenger.school_class_id:
        raise ValueError("Duel uchun sinfga biriktirilgan bo'lishingiz kerak.")
    if question_count not in rules.QUESTION_COUNTS:
        raise ValueError("Savollar soni 5, 10 yoki 15 bo'lishi mumkin.")

    if ai_level:
        if ai_level not in rules.AI_OPPONENTS:
            raise ValueError("Bunday AI raqib yo'q.")
        mode = Duel.Mode.AI
        opponent = None
        difficulty = rules.AI_OPPONENTS[ai_level]["difficulty"]
    else:
        if opponent is None:
            raise ValueError("Raqibni tanlang.")
        if opponent.pk == challenger.pk:
            raise ValueError("O'zingizni duelga chaqira olmaysiz.")
        if opponent.school_class_id != challenger.school_class_id:
            raise ValueError("Faqat sinfdoshingizni duelga chaqira olasiz.")
        already_open = Duel.objects.filter(status__in=OPEN_STATUSES).filter(
            Q(challenger=challenger, opponent=opponent) | Q(challenger=opponent, opponent=challenger)
        )
        if already_open.exists():
            raise ValueError("Bu sinfdoshingiz bilan ochiq duelingiz bor — avval uni tugating.")
        mode = Duel.Mode.CLASSMATE

    duel_questions = _pick_questions(subject=subject, student=challenger, count=question_count)

    duel = Duel.objects.create(
        mode=mode,
        ai_level=ai_level if mode == Duel.Mode.AI else "",
        challenger=challenger,
        opponent=opponent,
        school_class_id=challenger.school_class_id,
        subject=subject,
        difficulty=difficulty,
        # The bank may be thinner than asked for; record what was actually drawn
        # so the timer budget, the score and the invite text all agree.
        question_count=len(duel_questions),
        questions=duel_questions,
        rematch_of=rematch_of,
        status=Duel.Status.ACTIVE if mode == Duel.Mode.AI else Duel.Status.PENDING,
        accepted_at=timezone.now() if mode == Duel.Mode.AI else None,
    )

    if mode == Duel.Mode.CLASSMATE:
        notify(
            recipient=opponent.user,
            title="⚔️ Duel taklifi!",
            body=(
                f"{display_name(challenger)} sizni duelga chaqirdi: {subject.name}, "
                f"{duel.get_difficulty_display()}, {duel.question_count} ta savol. Qabul qilasizmi?"
            ),
            category=Notification.Category.DUEL_INVITE,
        )
    return duel


def _lock(duel: Duel) -> Duel:
    return Duel.objects.select_for_update().get(pk=duel.pk)


@transaction.atomic
def respond(*, duel: Duel, student, accept: bool) -> Duel:
    duel = _lock(duel)
    if duel.mode != Duel.Mode.CLASSMATE or duel.opponent_id != student.pk:
        raise ValueError("Bu taklif sizga emas.")
    if duel.status != Duel.Status.PENDING:
        raise ValueError("Bu taklif endi faol emas.")
    if accept:
        duel.status = Duel.Status.ACTIVE
        duel.accepted_at = timezone.now()
        duel.save(update_fields=["status", "accepted_at", "updated_at"])
        title, body = "Duel qabul qilindi!", f"{display_name(student)} taklifingizni qabul qildi — arenaga kiring."
    else:
        duel.status = Duel.Status.DECLINED
        duel.save(update_fields=["status", "updated_at"])
        title, body = "Duel rad etildi", f"{display_name(student)} bu safar duelni rad etdi."
    notify(recipient=duel.challenger.user, title=title, body=body, category=Notification.Category.DUEL_INVITE)
    return duel


@transaction.atomic
def cancel(*, duel: Duel, student) -> Duel:
    duel = _lock(duel)
    if duel.challenger_id != student.pk or duel.status != Duel.Status.PENDING:
        raise ValueError("Bu taklifni bekor qilib bo'lmaydi.")
    duel.status = Duel.Status.CANCELLED
    duel.save(update_fields=["status", "updated_at"])
    return duel


# ---------- The match ----------


@transaction.atomic
def mark_ready(*, duel: Duel, student) -> Duel:
    """Once both sides are ready (just the student, against the AI), the
    match starts after a short countdown — the same instant for both."""
    duel = _lock(duel)
    role = duel.role_of(student)
    if role is None:
        raise ValueError("Siz bu duel ishtirokchisi emassiz.")
    if duel.status != Duel.Status.ACTIVE:
        raise ValueError("Duel hali boshlanmagan yoki tugagan.")
    fields = ["updated_at"]
    if getattr(duel, f"{role}_ready_at") is None:
        setattr(duel, f"{role}_ready_at", timezone.now())
        fields.append(f"{role}_ready_at")
    both_ready = duel.mode == Duel.Mode.AI or (duel.challenger_ready_at and duel.opponent_ready_at)
    if both_ready and duel.match_starts_at is None:
        duel.match_starts_at = timezone.now() + timedelta(seconds=rules.COUNTDOWN_SECONDS)
        fields.append("match_starts_at")
    duel.save(update_fields=fields)
    return duel


def _answers(log: dict) -> dict:
    return log.get("answers") or {}


@transaction.atomic
def open_question(*, duel: Duel, student) -> dict:
    """The student's current question (answer-free), stamping when it was
    first shown — the server's clock times the answer, not the client's."""
    duel = _lock(duel)
    role = duel.role_of(student)
    if role is None:
        raise ValueError("Siz bu duel ishtirokchisi emassiz.")
    if duel.status != Duel.Status.ACTIVE or not duel.match_starts_at or timezone.now() < duel.match_starts_at:
        raise ValueError("Duel hali boshlanmadi.")
    log = getattr(duel, f"{role}_log") or {}
    index = len(_answers(log))
    if index >= len(duel.questions):
        return {"done": True}
    opened = log.setdefault("opened", {})
    if str(index) not in opened:
        opened[str(index)] = _now_ms()
        setattr(duel, f"{role}_log", log)
        duel.save(update_fields=[f"{role}_log", "updated_at"])
    question = duel.questions[index]
    return {
        "done": False,
        "index": index,
        "text": question["text"],
        "options": question["options"],
        "seconds": rules.SECONDS_PER_QUESTION[duel.difficulty],
        "opened_at_ms": opened[str(index)],
        "server_now_ms": _now_ms(),
    }


@transaction.atomic
def answer(*, duel: Duel, student, question_index: int, selected_index: int) -> dict:
    """Locks the answer in (strictly in order, once each) before revealing the
    key. Against the AI, its answer to the same question is logged right after
    — it never answers ahead of the student, so nothing leaks early."""
    duel = _lock(duel)
    role = duel.role_of(student)
    if role is None:
        raise ValueError("Siz bu duel ishtirokchisi emassiz.")
    if duel.status != Duel.Status.ACTIVE:
        raise ValueError("Bu duel faol emas.")
    log = getattr(duel, f"{role}_log") or {}
    answers = log.setdefault("answers", {})
    opened = log.get("opened") or {}
    if question_index != len(answers) or question_index >= len(duel.questions):
        raise ValueError("Noto'g'ri savol raqami.")
    if str(question_index) not in opened:
        raise ValueError("Savol hali ochilmagan.")
    question = duel.questions[question_index]
    if not (-1 <= selected_index < len(question["options"])):
        raise ValueError("Noto'g'ri javob varianti.")

    now = _now_ms()
    elapsed = now - opened[str(question_index)]
    answers[str(question_index)] = [selected_index, elapsed, now]
    setattr(duel, f"{role}_log", log)
    fields = [f"{role}_log", "updated_at"]
    if len(answers) == len(duel.questions):
        setattr(duel, f"{role}_submitted_at", timezone.now())
        fields.append(f"{role}_submitted_at")

    if duel.mode == Duel.Mode.AI:
        ai_log = duel.opponent_log or {}
        ai_answers = ai_log.setdefault("answers", {})
        ai_selected, ai_elapsed = rules.ai_answer(duel.pk, question_index, question, duel.ai_level)
        ai_answers[str(question_index)] = [ai_selected, ai_elapsed, opened[str(question_index)] + ai_elapsed]
        duel.opponent_log = ai_log
        fields.append("opponent_log")
        if len(ai_answers) == len(duel.questions):
            duel.opponent_submitted_at = timezone.now()
            fields.append("opponent_submitted_at")

    duel.save(update_fields=fields)
    if duel.challenger_submitted_at and duel.opponent_submitted_at:
        _finalize(duel)

    sides = battle(duel)
    limit = rules.limit_ms(duel.difficulty) + rules.GRACE_MS
    return {
        "correct": selected_index == question["correct_index"] and elapsed <= limit,
        "timed_out": elapsed > limit,
        "correct_index": question["correct_index"],
        "explanation": question.get("explanation", ""),
        "event": sides[role]["last"],
    }


def battle(duel: Duel) -> dict:
    return rules.battle_state(
        duel.questions, {"challenger": duel.challenger_log or {}, "opponent": duel.opponent_log or {}}, duel.difficulty
    )


# ---------- Finishing ----------


def _finalize(duel: Duel) -> None:
    """Called with the duel row locked. Decides the result from the replay and
    awards everything exactly once (the COMPLETED status guards re-entry)."""
    if duel.status == Duel.Status.COMPLETED:
        return
    sides = battle(duel)
    total = len(duel.questions) or 1
    duel.result = rules.result_of(sides)
    duel.status = Duel.Status.COMPLETED
    duel.completed_at = timezone.now()
    duel.challenger_score_percent = round(sides["challenger"]["correct"] / total * 100, 2)
    duel.opponent_score_percent = round(sides["opponent"]["correct"] / total * 100, 2)
    now = timezone.now()
    duel.challenger_submitted_at = duel.challenger_submitted_at or now
    duel.opponent_submitted_at = duel.opponent_submitted_at or now
    duel.save()
    _apply_ratings_and_rewards(duel, sides)


def _outcome_for(duel: Duel, role: str) -> str:
    if duel.result == Duel.Result.DRAW:
        return "DRAW"
    won = (duel.result == Duel.Result.CHALLENGER) == (role == "challenger")
    return "WIN" if won else "LOSS"


def _apply_ratings_and_rewards(duel: Duel, sides: dict) -> None:
    participants = [("challenger", duel.challenger)]
    if duel.opponent_id:
        participants.append(("opponent", duel.opponent))

    ratings = {role: get_or_create_rating(student) for role, student in participants}
    for role, rating in ratings.items():
        outcome = _outcome_for(duel, role)
        if outcome == "WIN":
            rating.wins += 1
        elif outcome == "LOSS":
            rating.losses += 1
        else:
            rating.draws += 1

    # The ELO-lite rating only moves between two real classmates.
    if duel.mode == Duel.Mode.CLASSMATE:
        challenger_actual = {"WIN": 1.0, "DRAW": 0.5, "LOSS": 0.0}[_outcome_for(duel, "challenger")]
        a, b = ratings["challenger"], ratings["opponent"]
        expected = 1 / (1 + 10 ** ((b.rating - a.rating) / 400))
        a.rating = max(0, round(a.rating + K_FACTOR * (challenger_actual - expected)))
        b.rating = max(0, round(b.rating + K_FACTOR * ((1 - challenger_actual) - (1 - expected))))
    for rating in ratings.values():
        rating.save()

    total = len(duel.questions) or 1
    opponent_label = {
        "challenger": display_name(duel.opponent) if duel.opponent_id else rules.AI_OPPONENTS[duel.ai_level]["name"],
        "opponent": display_name(duel.challenger),
    }
    for role, student in participants:
        outcome = _outcome_for(duel, role)
        xp = round(rules.MAX_ANSWER_XP * sides[role]["correct"] / total) + rules.RESULT_XP[outcome]
        if xp > 0:
            award_xp(
                student=student,
                amount=xp,
                source=XPTransaction.Source.DUEL,
                related_object=duel,
                reason=f"Duel: {opponent_label[role]}",
            )
        if outcome == "WIN" and duel_stats(student)["current_streak"] == rules.STREAK_BONUS_AT:
            award_xp(
                student=student,
                amount=rules.STREAK_BONUS_XP,
                source=XPTransaction.Source.DUEL,
                related_object=duel,
                reason=f"Duel: {rules.STREAK_BONUS_AT} ta ketma-ket g'alaba",
            )
        if duel.mode == Duel.Mode.CLASSMATE:
            label = {"WIN": "G'alaba! 🏆", "DRAW": "Durang 🤝", "LOSS": "Duel yakunlandi"}[outcome]
            notify(
                recipient=student.user,
                title=label,
                body=f"{opponent_label[role]} bilan duel: {sides[role]['correct']}/{total} to'g'ri javob.",
                category=Notification.Category.DUEL_RESULT,
            )


@transaction.atomic
def settle_if_stale(duel: Duel) -> Duel:
    """Invitations lapse after a day; a match nobody finishes is closed once
    its last question's time has long run out (unanswered = wrong), so a
    student who walks away can't leave a duel hanging forever."""
    if duel.status not in OPEN_STATUSES:
        return duel
    now = timezone.now()
    if duel.status == Duel.Status.PENDING:
        if now - duel.created_at > INVITE_TTL:
            duel = _lock(duel)
            if duel.status == Duel.Status.PENDING:
                duel.status = Duel.Status.EXPIRED
                duel.save(update_fields=["status", "updated_at"])
        return duel
    if duel.match_starts_at:
        per_question = timedelta(milliseconds=rules.limit_ms(duel.difficulty) + rules.GRACE_MS)
        deadline = duel.match_starts_at + per_question * len(duel.questions) + STALE_MATCH_SLACK
        if now > deadline:
            duel = _lock(duel)
            _finalize(duel)
    elif duel.accepted_at and now - duel.accepted_at > INVITE_TTL:
        duel = _lock(duel)
        if duel.status == Duel.Status.ACTIVE and not duel.match_starts_at:
            duel.status = Duel.Status.EXPIRED
            duel.save(update_fields=["status", "updated_at"])
    return duel


@transaction.atomic
def rematch(*, duel: Duel, student) -> Duel:
    role = duel.role_of(student)
    if role is None or duel.status != Duel.Status.COMPLETED:
        raise ValueError("Revansh faqat tugagan duelingiz uchun.")
    opponent = None
    if duel.mode == Duel.Mode.CLASSMATE:
        opponent = duel.opponent if role == "challenger" else duel.challenger
    return create_duel(
        challenger=student,
        opponent=opponent,
        ai_level=duel.ai_level,
        subject=duel.subject,
        difficulty=duel.difficulty,
        question_count=duel.question_count,
        rematch_of=duel,
    )


# ---------- Stats ----------


def duels_of(student):
    return Duel.objects.filter(Q(challenger=student) | Q(opponent=student))


def duel_stats(student) -> dict:
    """Wins, losses, draws and streaks, counted from finished duels only —
    nothing here can be set directly."""
    finished = duels_of(student).filter(status=Duel.Status.COMPLETED).order_by("completed_at", "id")
    wins = losses = draws = current = best = 0
    for duel in finished.only("challenger_id", "opponent_id", "result"):
        outcome = _outcome_for(duel, duel.role_of(student))
        if outcome == "WIN":
            wins += 1
            current += 1
            best = max(best, current)
        else:
            current = 0
            if outcome == "LOSS":
                losses += 1
            else:
                draws += 1
    xp = (
        XPTransaction.objects.filter(student=student, source=XPTransaction.Source.DUEL).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )
    rating = get_or_create_rating(student)
    return {
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "played": wins + losses + draws,
        "current_streak": current,
        "best_streak": best,
        "xp": xp,
        "rating": rating.rating,
    }


def xp_for_duel(duel: Duel, student) -> int:
    from django.contrib.contenttypes.models import ContentType

    return (
        XPTransaction.objects.filter(
            student=student,
            source=XPTransaction.Source.DUEL,
            content_type=ContentType.objects.get_for_model(Duel),
            object_id=duel.pk,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
