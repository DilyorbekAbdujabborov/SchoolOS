import random

from django.db import transaction
from django.utils import timezone

from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp
from apps.learning.models import Question
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import Duel, DuelAnswer, DuelQuestion, DuelRating

QUESTIONS_PER_DUEL = 5
MAX_DUEL_XP = 40
K_FACTOR = 32


def get_or_create_rating(student) -> DuelRating:
    rating, _created = DuelRating.objects.get_or_create(student=student)
    return rating


@transaction.atomic
def start_duel(*, challenger, opponent) -> Duel:
    """Creates the duel and snapshots a random question set drawn from the
    challenger's class's own published tests — so a duel is always fair
    (both students are eligible for the same material) without needing to
    tie the duel to one specific `Test`.
    """
    if challenger.pk == opponent.pk:
        raise ValueError("O'zingizni duelga chaqira olmaysiz.")
    if not challenger.school_class_id or challenger.school_class_id != opponent.school_class_id:
        raise ValueError("Faqat sinfdoshingizni duelga chaqira olasiz.")

    question_ids = list(
        Question.objects.filter(
            test__school_class_id=challenger.school_class_id, test__is_published=True
        )
        .values_list("id", flat=True)
        .distinct()
    )
    if len(question_ids) < QUESTIONS_PER_DUEL:
        raise ValueError(
            "Duel uchun yetarli savol yo'q — sinfingizda hali ko'proq test e'lon qilinishi kerak."
        )

    chosen_ids = random.sample(question_ids, QUESTIONS_PER_DUEL)

    duel = Duel.objects.create(
        challenger=challenger, opponent=opponent, school_class_id=challenger.school_class_id
    )
    DuelQuestion.objects.bulk_create(
        DuelQuestion(duel=duel, question_id=question_id, order=index + 1)
        for index, question_id in enumerate(chosen_ids)
    )

    notify(
        recipient=opponent.user,
        title="Yangi duel! ⚡",
        body=f"{challenger} sizni duelga chaqirdi. Javob berishga tayyormisiz?",
        category=Notification.Category.DUEL_INVITE,
    )
    return duel


@transaction.atomic
def start_participant(*, duel: Duel, participant) -> Duel:
    """Marks when a participant first opened the duel — used as their timing
    baseline if they never explicitly started it before submitting.
    """
    role = duel.role_of(participant)
    if role is None:
        raise ValueError("Siz bu duel ishtirokchisi emassiz.")

    field = f"{role}_started_at"
    if getattr(duel, field) is None:
        setattr(duel, field, timezone.now())
        duel.save(update_fields=[field, "updated_at"])
    return duel


@transaction.atomic
def submit_duel_answers(*, duel: Duel, participant, answers: list[dict]) -> Duel:
    role = duel.role_of(participant)
    if role is None:
        raise ValueError("Siz bu duel ishtirokchisi emassiz.")
    if duel.status != Duel.Status.ACTIVE:
        raise ValueError("Bu duel yakunlangan.")

    submitted_field = f"{role}_submitted_at"
    if getattr(duel, submitted_field) is not None:
        raise ValueError("Siz bu duelda allaqachon javob yuborgansiz.")

    question_ids = set(duel.duel_questions.values_list("question_id", flat=True))
    answer_map = {answer["question"].id: answer["selected_option"] for answer in answers}

    correct = 0
    for question_id in question_ids:
        selected_option = answer_map.get(question_id)
        if selected_option is None:
            continue
        DuelAnswer.objects.update_or_create(
            duel=duel,
            participant=participant,
            question_id=question_id,
            defaults={"selected_option": selected_option, "is_correct": selected_option.is_correct},
        )
        if selected_option.is_correct:
            correct += 1

    total = len(question_ids)
    score_percent = round((correct / total) * 100, 2) if total else 0.0

    started_field = f"{role}_started_at"
    if getattr(duel, started_field) is None:
        setattr(duel, started_field, duel.created_at)

    setattr(duel, f"{role}_score_percent", score_percent)
    setattr(duel, submitted_field, timezone.now())
    duel.save(update_fields=[f"{role}_score_percent", submitted_field, started_field, "updated_at"])

    if duel.challenger_submitted_at and duel.opponent_submitted_at:
        _finalize_duel(duel)

    return duel


def _elapsed_seconds(started_at, submitted_at) -> float:
    if not started_at or not submitted_at:
        return float("inf")
    return (submitted_at - started_at).total_seconds()


@transaction.atomic
def _finalize_duel(duel: Duel) -> None:
    challenger_time = _elapsed_seconds(duel.challenger_started_at, duel.challenger_submitted_at)
    opponent_time = _elapsed_seconds(duel.opponent_started_at, duel.opponent_submitted_at)

    if duel.challenger_score_percent > duel.opponent_score_percent:
        result = Duel.Result.CHALLENGER
    elif duel.opponent_score_percent > duel.challenger_score_percent:
        result = Duel.Result.OPPONENT
    elif challenger_time < opponent_time:
        result = Duel.Result.CHALLENGER
    elif opponent_time < challenger_time:
        result = Duel.Result.OPPONENT
    else:
        result = Duel.Result.DRAW

    duel.result = result
    duel.status = Duel.Status.COMPLETED
    duel.completed_at = timezone.now()
    duel.save(update_fields=["result", "status", "completed_at", "updated_at"])

    _apply_rating_and_xp(duel, result)


def _apply_rating_and_xp(duel: Duel, result: str) -> None:
    challenger_rating = get_or_create_rating(duel.challenger)
    opponent_rating = get_or_create_rating(duel.opponent)

    if result == Duel.Result.DRAW:
        challenger_actual, opponent_actual = 0.5, 0.5
        challenger_rating.draws += 1
        opponent_rating.draws += 1
    elif result == Duel.Result.CHALLENGER:
        challenger_actual, opponent_actual = 1.0, 0.0
        challenger_rating.wins += 1
        opponent_rating.losses += 1
    else:
        challenger_actual, opponent_actual = 0.0, 1.0
        challenger_rating.losses += 1
        opponent_rating.wins += 1

    expected_challenger = 1 / (1 + 10 ** ((opponent_rating.rating - challenger_rating.rating) / 400))
    expected_opponent = 1 - expected_challenger

    challenger_rating.rating = max(
        0, round(challenger_rating.rating + K_FACTOR * (challenger_actual - expected_challenger))
    )
    opponent_rating.rating = max(
        0, round(opponent_rating.rating + K_FACTOR * (opponent_actual - expected_opponent))
    )
    challenger_rating.save()
    opponent_rating.save()

    for student, score_percent in (
        (duel.challenger, duel.challenger_score_percent),
        (duel.opponent, duel.opponent_score_percent),
    ):
        xp_awarded = round(MAX_DUEL_XP * (score_percent or 0) / 100)
        if xp_awarded > 0:
            award_xp(
                student=student,
                amount=xp_awarded,
                source=XPTransaction.Source.DUEL,
                related_object=duel,
                reason="Duel natijasi",
            )

    outcome_label = {
        Duel.Result.DRAW: "Durang bo'ldi.",
        Duel.Result.CHALLENGER: f"{duel.challenger} g'alaba qozondi.",
        Duel.Result.OPPONENT: f"{duel.opponent} g'alaba qozondi.",
    }[result]
    for recipient, my_score in (
        (duel.challenger, duel.challenger_score_percent),
        (duel.opponent, duel.opponent_score_percent),
    ):
        notify(
            recipient=recipient.user,
            title="Duel yakunlandi",
            body=f"{outcome_label} Sizning natijangiz: {my_score:.0f}%.",
            category=Notification.Category.DUEL_RESULT,
        )
