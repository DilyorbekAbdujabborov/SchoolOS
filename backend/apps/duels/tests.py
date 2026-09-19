from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import make_school_class, make_student, make_subject, make_teacher
from apps.gamification.models import XPTransaction
from apps.learning.models import Option, Question, Test
from apps.notifications.models import Notification

from .models import Duel, DuelRating
from .services import start_duel, submit_duel_answers


def _make_published_test_with_questions(*, school_class, subject, teacher, count: int) -> Test:
    test = Test.objects.create(
        title=f"Test-{subject.name}", subject=subject, school_class=school_class, teacher=teacher,
        is_published=True,
    )
    for index in range(count):
        question = Question.objects.create(test=test, text=f"Savol {index + 1}?", order=index + 1)
        Option.objects.create(question=question, text="To'g'ri", is_correct=True)
        Option.objects.create(question=question, text="Xato", is_correct=False)
    return test


def _all_correct_answers(duel: Duel) -> list[dict]:
    return [
        {"question": dq.question, "selected_option": dq.question.options.get(is_correct=True)}
        for dq in duel.duel_questions.all()
    ]


def _all_wrong_answers(duel: Duel) -> list[dict]:
    return [
        {"question": dq.question, "selected_option": dq.question.options.get(is_correct=False)}
        for dq in duel.duel_questions.all()
    ]


class DuelServiceTests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.school_class = make_school_class()
        self.a_user, self.a = make_student(self.school_class)
        self.b_user, self.b = make_student(self.school_class)
        _make_published_test_with_questions(
            school_class=self.school_class, subject=self.subject, teacher=self.teacher, count=5
        )

    def test_cannot_duel_yourself(self):
        with self.assertRaises(ValueError):
            start_duel(challenger=self.a, opponent=self.a)

    def test_cannot_duel_a_student_in_another_class(self):
        other_class = make_school_class()
        _, outsider = make_student(other_class)
        with self.assertRaises(ValueError):
            start_duel(challenger=self.a, opponent=outsider)

    def test_needs_at_least_five_published_questions(self):
        empty_class = make_school_class()
        _, x = make_student(empty_class)
        _, y = make_student(empty_class)
        with self.assertRaises(ValueError):
            start_duel(challenger=x, opponent=y)

    def test_duel_snapshots_five_questions(self):
        duel = start_duel(challenger=self.a, opponent=self.b)
        self.assertEqual(duel.duel_questions.count(), 5)
        self.assertEqual(duel.status, Duel.Status.ACTIVE)

    def test_invite_notification_sent_to_opponent(self):
        start_duel(challenger=self.a, opponent=self.b)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.b_user, category=Notification.Category.DUEL_INVITE
            ).exists()
        )

    def test_higher_score_wins_and_awards_xp(self):
        duel = start_duel(challenger=self.a, opponent=self.b)
        submit_duel_answers(duel=duel, participant=self.a, answers=_all_correct_answers(duel))
        duel.refresh_from_db()
        self.assertEqual(duel.status, Duel.Status.ACTIVE)  # only one side has submitted so far

        submit_duel_answers(duel=duel, participant=self.b, answers=_all_wrong_answers(duel))
        duel.refresh_from_db()

        self.assertEqual(duel.status, Duel.Status.COMPLETED)
        self.assertEqual(duel.result, Duel.Result.CHALLENGER)
        self.assertTrue(XPTransaction.objects.filter(student=self.a, source=XPTransaction.Source.DUEL).exists())

        a_rating = DuelRating.objects.get(student=self.a)
        b_rating = DuelRating.objects.get(student=self.b)
        self.assertGreater(a_rating.rating, DuelRating.DEFAULT_RATING)
        self.assertLess(b_rating.rating, DuelRating.DEFAULT_RATING)
        self.assertEqual(a_rating.wins, 1)
        self.assertEqual(b_rating.losses, 1)

    def test_faster_participant_wins_on_a_score_tie(self):
        duel = start_duel(challenger=self.a, opponent=self.b)
        duel.challenger_started_at = timezone.now() - timezone.timedelta(seconds=120)
        duel.opponent_started_at = timezone.now() - timezone.timedelta(seconds=10)
        duel.save(update_fields=["challenger_started_at", "opponent_started_at"])

        submit_duel_answers(duel=duel, participant=self.a, answers=_all_correct_answers(duel))
        submit_duel_answers(duel=duel, participant=self.b, answers=_all_correct_answers(duel))
        duel.refresh_from_db()

        self.assertEqual(duel.result, Duel.Result.OPPONENT)  # b started later but tied on score -> faster wins

    def test_cannot_submit_twice(self):
        duel = start_duel(challenger=self.a, opponent=self.b)
        submit_duel_answers(duel=duel, participant=self.a, answers=_all_correct_answers(duel))
        with self.assertRaises(ValueError):
            submit_duel_answers(duel=duel, participant=self.a, answers=_all_correct_answers(duel))


class DuelAPITests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.school_class = make_school_class()
        self.a_user, self.a = make_student(self.school_class)
        self.b_user, self.b = make_student(self.school_class)
        self.c_user, self.c = make_student(self.school_class)
        _make_published_test_with_questions(
            school_class=self.school_class, subject=self.subject, teacher=self.teacher, count=5
        )

    def test_student_can_create_a_duel(self):
        self.client.force_authenticate(self.a_user)
        response = self.client.post("/api/duels/", {"opponent": self.b.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["my_role"], "challenger")

    def test_teacher_cannot_create_a_duel(self):
        self.client.force_authenticate(self.teacher.user)
        response = self.client.post("/api/duels/", {"opponent": self.b.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bystander_cannot_see_or_submit_to_a_duel_they_are_not_in(self):
        self.client.force_authenticate(self.a_user)
        create_response = self.client.post("/api/duels/", {"opponent": self.b.id}, format="json")
        duel_id = create_response.data["id"]

        self.client.force_authenticate(self.c_user)
        response = self.client.get(f"/api/duels/{duel_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_duel_flow_via_api(self):
        self.client.force_authenticate(self.a_user)
        create_response = self.client.post("/api/duels/", {"opponent": self.b.id}, format="json")
        duel_id = create_response.data["id"]

        questions_response = self.client.get(f"/api/duels/{duel_id}/questions/")
        self.assertEqual(questions_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(questions_response.data), 5)

        answers = [
            {"question": q["id"], "selected_option": q["options"][0]["id"]} for q in questions_response.data
        ]
        submit_response = self.client.post(f"/api/duels/{duel_id}/submit/", {"answers": answers}, format="json")
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertTrue(submit_response.data["i_have_submitted"])
        self.assertFalse(submit_response.data["opponent_has_submitted"])

        self.client.force_authenticate(self.b_user)
        opponents_response = self.client.get("/api/duels/opponents/")
        self.assertEqual(opponents_response.status_code, status.HTTP_200_OK)
        self.assertEqual({o["id"] for o in opponents_response.data}, {self.a.id, self.c.id})

        rating_response = self.client.get("/api/duels/me/")
        self.assertEqual(rating_response.status_code, status.HTTP_200_OK)
        self.assertEqual(rating_response.data["rating"], DuelRating.DEFAULT_RATING)
