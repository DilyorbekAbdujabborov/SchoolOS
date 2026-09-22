import json
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import make_director, make_school_class, make_student, make_subject, make_teacher
from apps.gamification.models import XPTransaction

from .models import GameSession, PooledQuestion
from .services import (
    POOL_LOW_THRESHOLD,
    check_answer,
    pick_session_questions,
    pool_status,
    refill_pool,
    start_game,
    submit_game,
)
from .tasks import refill_low_pools


def _gemini_response(content: str) -> Mock:
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"candidates": [{"content": {"parts": [{"text": content}]}}]}
    return response


def _questions_payload(count: int) -> str:
    return json.dumps(
        {
            "questions": [
                {"text": f"Savol {i}", "options": ["a", "b", "c", "d"], "correct_index": i % 4}
                for i in range(count)
            ]
        }
    )


def _seed_pool(*, subject, school_class, count: int) -> list[PooledQuestion]:
    return PooledQuestion.objects.bulk_create(
        PooledQuestion(
            subject=subject,
            school_class=school_class,
            text=f"Savol {i}",
            options=["a", "b", "c", "d"],
            correct_index=i % 4,
        )
        for i in range(count)
    )


class PoolPickingTests(APITestCase):
    """`pick_session_questions` never talks to Gemini — see GameAPITests for
    the end-to-end proof that a game start doesn't call it either.
    """

    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)

    def test_picks_eight_questions_from_a_larger_pool(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        session = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)

        questions = pick_session_questions(session)

        self.assertEqual(len(questions), 8)

    def test_returns_none_when_pool_too_small(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=5)
        session = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)

        self.assertIsNone(pick_session_questions(session))

    def test_returns_none_when_student_has_no_class(self):
        _, unassigned_student = make_student(school_class=None)
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        session = start_game(
            student=unassigned_student, subject=self.subject, game_type=GameSession.GameType.QUIZ
        )

        self.assertIsNone(pick_session_questions(session))

    def test_scoped_to_the_exact_class_not_just_the_subject(self):
        other_class = make_school_class()
        _seed_pool(subject=self.subject, school_class=other_class, count=20)
        session = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)

        # self.student is in self.school_class, but the pool was seeded for other_class.
        self.assertIsNone(pick_session_questions(session))

    def test_avoids_repeats_across_two_games_when_pool_is_large_enough(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=16)

        first = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        first_questions = pick_session_questions(first)

        second = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        second_questions = pick_session_questions(second)

        first_texts = {q["text"] for q in first_questions}
        second_texts = {q["text"] for q in second_questions}
        self.assertEqual(first_texts & second_texts, set())

    def test_falls_back_to_repeats_when_the_pool_is_exhausted(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=8)

        first = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        pick_session_questions(first)

        second = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        second_questions = pick_session_questions(second)

        # Only 8 questions exist total, so a second game for the same student
        # has no choice but to repeat them — better than refusing to play.
        self.assertEqual(len(second_questions), 8)

    def test_idempotent_for_the_same_session(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        session = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)

        first_call = pick_session_questions(session)
        second_call = pick_session_questions(session)

        self.assertEqual(first_call, second_call)


class PoolRefillTests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key")
    @patch("apps.common.gemini.requests.post")
    def test_refill_adds_valid_questions_and_skips_malformed_ones(self, mock_post):
        payload = json.dumps(
            {
                "questions": [
                    {"text": "Yaxshi savol", "options": ["a", "b", "c", "d"], "correct_index": 1},
                    {"text": "", "options": ["a", "b"], "correct_index": 0},  # empty text
                    {"text": "Noto'g'ri indeks", "options": ["a", "b"], "correct_index": 5},  # out of range
                    {"text": "Kam variant", "options": ["a"], "correct_index": 0},  # < 2 options
                ]
            }
        )
        mock_post.return_value = _gemini_response(payload)

        added = refill_pool(subject=self.subject, school_class=self.school_class, batch_size=4)

        self.assertEqual(added, 1)
        self.assertEqual(PooledQuestion.objects.count(), 1)

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "")
    @patch("apps.common.gemini.settings.GROQ_API_KEY", "")
    def test_refill_returns_zero_when_gemini_is_unavailable(self):
        # No API key configured for either provider — call_gemini short-circuits to None.
        added = refill_pool(subject=self.subject, school_class=self.school_class)

        self.assertEqual(added, 0)
        self.assertEqual(PooledQuestion.objects.count(), 0)

    def test_pool_status_reports_counts_per_subject_and_class(self):
        other_class = make_school_class()
        _seed_pool(subject=self.subject, school_class=self.school_class, count=3)
        _seed_pool(subject=self.subject, school_class=other_class, count=5)

        rows = {(r["school_class"], r["count"]) for r in pool_status()}

        self.assertIn((self.school_class.id, 3), rows)
        self.assertIn((other_class.id, 5), rows)


class RefillLowPoolsTaskTests(APITestCase):
    """Regression: `refill_low_pools` used to fetch each low pool's Subject
    and SchoolClass with two separate `.get()` calls per row (N+1) — this
    also guards that the batch-fetched dict lookup doesn't mix up which
    subject/class pair gets refilled."""

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key")
    @patch("apps.common.gemini.requests.post")
    def test_refills_every_low_pool_and_keeps_subject_class_pairs_correct(self, mock_post):
        subject_a, class_a = make_subject(), make_school_class()
        subject_b, class_b = make_subject(), make_school_class()
        _seed_pool(subject=subject_a, school_class=class_a, count=5)
        _seed_pool(subject=subject_b, school_class=class_b, count=5)
        # Not low — must be left alone.
        subject_c, class_c = make_subject(), make_school_class()
        _seed_pool(subject=subject_c, school_class=class_c, count=POOL_LOW_THRESHOLD)

        payload = json.dumps(
            {
                "questions": [
                    {"text": f"Savol {i}", "options": ["a", "b", "c", "d"], "correct_index": 0}
                    for i in range(30)
                ]
            }
        )
        mock_post.return_value = _gemini_response(payload)

        refilled = refill_low_pools()

        self.assertEqual(refilled, 2)
        self.assertGreater(PooledQuestion.objects.filter(subject=subject_a, school_class=class_a).count(), 5)
        self.assertGreater(PooledQuestion.objects.filter(subject=subject_b, school_class=class_b).count(), 5)
        self.assertEqual(PooledQuestion.objects.filter(subject=subject_c, school_class=class_c).count(), 20)


class GameServiceTests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)

    def test_submit_scores_and_awards_xp(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=8)
        session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.TUG_OF_WAR
        )
        pick_session_questions(session)

        answers = {i: q["correct_index"] for i, q in enumerate(session.questions)}
        session = submit_game(session=session, answers=answers)

        self.assertEqual(session.score_percent, 100.0)
        self.assertEqual(session.status, GameSession.Status.COMPLETED)
        self.assertTrue(
            XPTransaction.objects.filter(student=self.student, source=XPTransaction.Source.GAME).exists()
        )

    def test_cannot_submit_before_questions_exist(self):
        session = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        with self.assertRaises(ValueError):
            submit_game(session=session, answers={0: 0})

    def test_check_answer_never_reveals_other_questions(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=8)
        session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.TUG_OF_WAR
        )
        pick_session_questions(session)

        correct_index = session.questions[0]["correct_index"]
        self.assertTrue(check_answer(session=session, question_index=0, selected_index=correct_index))
        self.assertFalse(check_answer(session=session, question_index=0, selected_index=(correct_index + 1) % 4))
        # A timeout sends -1, which never matches any option index.
        self.assertFalse(check_answer(session=session, question_index=0, selected_index=-1))

    def test_check_answer_rejects_out_of_range_question(self):
        session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.TUG_OF_WAR
        )
        session.questions = [{"text": "Q", "options": ["a", "b"], "correct_index": 0}]
        with self.assertRaises(ValueError):
            check_answer(session=session, question_index=5, selected_index=0)


class GameAPITests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)
        self.teacher_user = self.teacher.user

    def test_teacher_cannot_start_a_game(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "QUIZ"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_start_a_game(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "TUG_OF_WAR"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "ACTIVE")

    @patch("apps.games.services.call_gemini")
    def test_full_flow_never_calls_gemini(self, mock_gemini):
        """The core promise of the pool system: a game's live start is pure DB reads."""
        _seed_pool(subject=self.subject, school_class=self.school_class, count=8)
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "QUIZ"}, format="json"
        )
        session_id = create_response.data["id"]

        questions_response = self.client.get(f"/api/games/{session_id}/questions/")
        self.assertEqual(questions_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(questions_response.data), 8)
        self.assertNotIn("correct_index", questions_response.data[0])

        answer_response = self.client.post(
            f"/api/games/{session_id}/answer/", {"question_index": 0, "selected_index": 0}, format="json"
        )
        self.assertEqual(answer_response.status_code, status.HTTP_200_OK)
        self.assertIn("correct", answer_response.data)

        answers = [{"question_index": i, "selected_index": 0} for i in range(8)]
        submit_response = self.client.post(
            f"/api/games/{session_id}/submit/", {"answers": answers}, format="json"
        )
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(submit_response.data["status"], "COMPLETED")

        mock_gemini.assert_not_called()

    @patch("apps.games.services.call_gemini")
    def test_questions_endpoint_returns_503_when_pool_is_empty(self, mock_gemini):
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "QUIZ"}, format="json"
        )
        session_id = create_response.data["id"]

        response = self.client.get(f"/api/games/{session_id}/questions/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        mock_gemini.assert_not_called()

    def test_submitting_a_timed_out_question_is_accepted(self):
        """Regression: the frontend always includes every question in the
        submit payload, including ones the student timed out on (selected_index
        -1) — the "answer" endpoint has always accepted -1 for a timeout, but
        the submit serializer rejected it with min_value=0, so any game where
        the student let the clock run out on even one question could never
        be submitted at all (400 on every attempt, no XP, no saved result)."""
        _seed_pool(subject=self.subject, school_class=self.school_class, count=8)
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "TUG_OF_WAR"}, format="json"
        )
        session_id = create_response.data["id"]
        self.client.get(f"/api/games/{session_id}/questions/")

        answers = [{"question_index": 0, "selected_index": -1}] + [
            {"question_index": i, "selected_index": 0} for i in range(1, 8)
        ]
        submit_response = self.client.post(
            f"/api/games/{session_id}/submit/", {"answers": answers}, format="json"
        )

        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(submit_response.data["status"], "COMPLETED")

    def test_student_cannot_access_another_students_session(self):
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "QUIZ"}, format="json"
        )
        session_id = create_response.data["id"]

        other_user, _other = make_student(self.school_class)
        self.client.force_authenticate(other_user)
        response = self.client.get(f"/api/games/{session_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuestionPoolAPITests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.director_user = make_director()
        _, self.teacher = make_teacher()
        self.student_user, _ = make_student(self.school_class)

    def test_student_cannot_list_or_refill_pools(self):
        self.client.force_authenticate(self.student_user)
        self.assertEqual(self.client.get("/api/question-pools/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.post(
                "/api/question-pools/refill/",
                {"subject": self.subject.id, "school_class": self.school_class.id},
                format="json",
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_teacher_cannot_list_or_refill_pools(self):
        self.client.force_authenticate(self.teacher.user)
        self.assertEqual(self.client.get("/api/question-pools/").status_code, status.HTTP_403_FORBIDDEN)

    def test_director_can_list_pools(self):
        _seed_pool(subject=self.subject, school_class=self.school_class, count=6)
        self.client.force_authenticate(self.director_user)

        response = self.client.get("/api/question-pools/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["count"], 6)

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key")
    @patch("apps.common.gemini.requests.post")
    def test_director_can_refill_a_pool(self, mock_post):
        mock_post.return_value = _gemini_response(_questions_payload(10))
        self.client.force_authenticate(self.director_user)

        response = self.client.post(
            "/api/question-pools/refill/",
            {"subject": self.subject.id, "school_class": self.school_class.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added"], 10)
        self.assertEqual(PooledQuestion.objects.count(), 10)
