import json

from django.db import transaction
from django.utils import timezone

from apps.academics.models import TimetableSlot
from apps.common.gemini import call_gemini
from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import (
    LOW_FREQUENCY_QUESTION_CAP,
    LOW_FREQUENCY_WEEKLY_LESSON_THRESHOLD,
    ActivityResult,
    ActivitySubmission,
    Option,
    Question,
    Test,
    TestAnswer,
    TestAttempt,
)


@transaction.atomic
def grade_attempt(*, attempt: TestAttempt, answers: list[dict]) -> TestAttempt:
    """Scores an attempt from the student's answers and awards XP for it.

    `answers` is `[{"question": Question, "selected_option": Option}, ...]`
    (already resolved + cross-validated by `TestSubmitSerializer`). The score
    is computed purely from `Option.is_correct` here — the client never sends
    a score or an XP amount, so there is nothing for it to manipulate.
    """
    if attempt.status == TestAttempt.Status.SUBMITTED:
        raise ValueError("This attempt has already been submitted.")

    questions = list(attempt.test.questions.all())
    answer_map = {answer["question"].id: answer["selected_option"] for answer in answers}

    correct = 0
    for question in questions:
        selected_option = answer_map.get(question.id)
        if selected_option is None:
            continue
        TestAnswer.objects.update_or_create(
            attempt=attempt, question=question, defaults={"selected_option": selected_option}
        )
        if selected_option.is_correct:
            correct += 1

    total = len(questions)
    score_percent = round((correct / total) * 100, 2) if total else 0.0
    xp_awarded = round(attempt.test.max_xp * score_percent / 100)

    attempt.status = TestAttempt.Status.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.score_percent = score_percent
    attempt.xp_awarded = xp_awarded
    attempt.save(
        update_fields=["status", "submitted_at", "score_percent", "xp_awarded", "updated_at"]
    )

    award_xp(
        student=attempt.student,
        amount=xp_awarded,
        source=XPTransaction.Source.TEST,
        related_object=attempt.test,
        reason=f"Test: {attempt.test.title}",
    )

    notify(
        recipient=attempt.student.user,
        title=f"{attempt.test.title} — natija",
        body=f"Siz {score_percent:.0f}% to'plabsiz va {xp_awarded} XP oldingiz.",
        category=Notification.Category.TEST_RESULT,
    )

    return attempt


def notify_class_of_new_test(test) -> None:
    """Tells every student in the class a new test is available to take."""
    for student in test.school_class.students.select_related("user"):
        notify(
            recipient=student.user,
            title="Yangi test e'lon qilindi",
            body=f"{test.subject.name}: \"{test.title}\" — endi topshirishingiz mumkin.",
            category=Notification.Category.TEST_PUBLISHED,
        )


@transaction.atomic
def grade_submission(
    *, submission: ActivitySubmission, score_percent: float, feedback: str, graded_by
) -> ActivityResult:
    """Grades a submission and awards XP for it — same "server computes XP,
    never trusts a number from the client" rule as `grade_attempt`, except
    here the score itself is a teacher's judgment call rather than an
    auto-graded multiple-choice tally.
    """
    if hasattr(submission, "result"):
        raise ValueError("This submission has already been graded.")
    if not 0 <= score_percent <= 100:
        raise ValueError("score_percent must be between 0 and 100.")

    xp_awarded = round(submission.activity.max_xp * score_percent / 100)

    result = ActivityResult.objects.create(
        submission=submission,
        score_percent=score_percent,
        xp_awarded=xp_awarded,
        feedback=feedback,
        graded_by=graded_by,
    )

    award_xp(
        student=submission.student,
        amount=xp_awarded,
        source=XPTransaction.Source.ACTIVITY,
        related_object=submission.activity,
        reason=f"Activity: {submission.activity.title}",
    )

    notify(
        recipient=submission.student.user,
        title=f"{submission.activity.title} — baholandi",
        body=f"Siz {score_percent:.0f}% to'plabsiz va {xp_awarded} XP oldingiz.",
        category=Notification.Category.ACTIVITY_RESULT,
    )

    return result


def notify_class_of_new_activity(activity) -> None:
    """Tells every student in the class a new activity is available."""
    for student in activity.school_class.students.select_related("user"):
        notify(
            recipient=student.user,
            title="Yangi topshiriq e'lon qilindi",
            body=f"{activity.subject.name}: \"{activity.title}\" — endi bajarishingiz mumkin.",
            category=Notification.Category.ACTIVITY_PUBLISHED,
        )


@transaction.atomic
def generate_test_with_ai(
    *,
    teacher,
    title: str,
    subject,
    school_class,
    topic: str,
    question_count: int,
    max_xp: int,
    time_limit_minutes: int | None,
) -> Test:
    """Drafts a full multiple-choice test from a one-line topic — saves a
    teacher from typing out every question by hand. The result is a normal,
    fully-editable `Test` (draft, unpublished) with real `Question`/`Option`
    rows, exactly as if the teacher had typed it in themselves; nothing about
    it is AI-flavored once it's saved.

    Respects the same low-weekly-frequency question cap as manual creation
    (see `LOW_FREQUENCY_QUESTION_CAP`) — a subject that barely meets doesn't
    get a 20-question AI test just because generating them is easy.
    """
    weekly_lessons = TimetableSlot.objects.filter(school_class=school_class, subject=subject).count()
    if 0 < weekly_lessons <= LOW_FREQUENCY_WEEKLY_LESSON_THRESHOLD:
        question_count = min(question_count, LOW_FREQUENCY_QUESTION_CAP)

    prompt = (
        f'"{subject.name}" fani, "{topic}" mavzusi bo\'yicha {school_class.name} sinfi uchun {question_count} ta '
        "test savoli tuzib ber. Har savolda aniq 4 ta variant va faqat bitta to'g'ri javob bo'lsin, savollar "
        "turli qiyinlik darajasida (ba'zilari oson, ba'zilari qiyinroq) bo'lsin.\n\n"
        "Faqat quyidagi JSON formatida javob ber, boshqa hech narsa yozma:\n"
        '{"questions": [{"text": "...", "options": ["...", "...", "...", "..."], "correct_index": 0}]}\n'
        "Hammasi o'zbek tilida bo'lsin."
    )

    content = call_gemini(prompt=prompt, json_mode=True)
    if content is None:
        raise ValueError("AI hozircha javob bera olmadi. Birozdan so'ng qayta urinib ko'ring.")

    try:
        questions = json.loads(content)["questions"]
        if not isinstance(questions, list) or not questions:
            raise ValueError
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("AI natijasini o'qib bo'lmadi. Qayta urinib ko'ring.") from exc

    # The prompt already asks for `question_count`, but never trust the AI to
    # actually respect that — enforce the cap in code, not just in English (well, Uzbek).
    questions = questions[:question_count]

    test = Test.objects.create(
        title=title,
        subject=subject,
        school_class=school_class,
        teacher=teacher,
        max_xp=max_xp,
        time_limit_minutes=time_limit_minutes,
    )
    for order, question_data in enumerate(questions, start=1):
        question = Question.objects.create(test=test, text=question_data["text"], order=order)
        correct_index = question_data.get("correct_index", 0)
        Option.objects.bulk_create(
            Option(question=question, text=option_text, is_correct=(index == correct_index))
            for index, option_text in enumerate(question_data["options"])
        )

    return test
