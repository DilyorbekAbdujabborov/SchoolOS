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
    record_live_answer,
    refill_pool,
    revealed_code,
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
                {
                    "text": f"Savol {i}",
                    "options": ["a", "b", "c", "d"],
                    "correct_index": i % 4,
                    "explanation": f"Izoh {i}",
                }
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
            explanation=f"Izoh {i}",
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


class TowerBuilderTests(APITestCase):
    """Minora qurish: ten questions, answers locked in one at a time server-side,
    the key revealed only after the answer is recorded, XP via the shared formula.
    """

    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        self.session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.TOWER_BUILDER
        )
        pick_session_questions(self.session)

    def _answer(self, index, *, correct):
        key = self.session.questions[index]["correct_index"]
        return record_live_answer(
            session=self.session, question_index=index, selected_index=key if correct else (key + 1) % 4
        )

    def test_picks_ten_questions(self):
        self.assertEqual(len(self.session.questions), 10)

    def test_other_games_still_pick_eight(self):
        quiz = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        self.assertEqual(len(pick_session_questions(quiz)), 8)

    def test_correct_answer_builds_a_floor_and_reports_running_xp(self):
        result = self._answer(0, correct=True)

        self.assertTrue(result["correct"])
        self.assertEqual(result["correct_count"], 1)
        self.assertEqual(result["answered_count"], 1)
        self.assertEqual(result["xp_earned"], 3)

    def test_wrong_answer_reveals_key_and_explanation_but_adds_no_floor(self):
        result = self._answer(0, correct=False)

        self.assertFalse(result["correct"])
        self.assertEqual(result["correct_index"], self.session.questions[0]["correct_index"])
        self.assertEqual(result["explanation"], self.session.questions[0]["explanation"])
        self.assertEqual(result["correct_count"], 0)
        self.assertEqual(result["xp_earned"], 0)

    def test_an_answer_cannot_be_changed_once_recorded(self):
        self._answer(0, correct=False)
        with self.assertRaises(ValueError):
            self._answer(0, correct=True)

    def test_questions_must_be_answered_in_order(self):
        with self.assertRaises(ValueError):
            self._answer(3, correct=True)

    def test_rejects_an_out_of_range_option(self):
        with self.assertRaises(ValueError):
            record_live_answer(session=self.session, question_index=0, selected_index=9)

    def test_other_game_types_cannot_record_answers(self):
        quiz = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        pick_session_questions(quiz)
        with self.assertRaises(ValueError):
            record_live_answer(session=quiz, question_index=0, selected_index=0)

    def test_submit_scores_the_recorded_answers_not_the_payload(self):
        for i in range(10):
            self._answer(i, correct=i < 7)
        self.session.refresh_from_db()

        # The client claims a perfect game — the server's own record wins.
        claimed = {i: q["correct_index"] for i, q in enumerate(self.session.questions)}
        session = submit_game(session=self.session, answers=claimed)

        self.assertEqual(session.score_percent, 70.0)
        self.assertEqual(session.xp_awarded, 21)
        transaction = XPTransaction.objects.get(student=self.student, source=XPTransaction.Source.GAME)
        self.assertEqual(transaction.amount, 21)

    def test_cannot_submit_before_every_question_is_answered(self):
        self._answer(0, correct=True)
        self.session.refresh_from_db()
        with self.assertRaises(ValueError):
            submit_game(session=self.session, answers={0: 0})

    def test_cannot_answer_after_completion(self):
        for i in range(10):
            self._answer(i, correct=True)
        self.session.refresh_from_db()
        submit_game(session=self.session, answers={0: 0})
        with self.assertRaises(ValueError):
            record_live_answer(session=self.session, question_index=0, selected_index=0)

    def test_api_flow_hides_the_key_until_answered_and_reports_progress(self):
        self.client.force_authenticate(self.student_user)
        questions = self.client.get(f"/api/games/{self.session.id}/questions/").data
        self.assertEqual(len(questions), 10)
        self.assertNotIn("correct_index", questions[0])
        self.assertNotIn("explanation", questions[0])

        response = self.client.post(
            f"/api/games/{self.session.id}/answer/", {"question_index": 0, "selected_index": -1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["correct"])
        self.assertIn("correct_index", response.data)

        repeat = self.client.post(
            f"/api/games/{self.session.id}/answer/", {"question_index": 0, "selected_index": 0}, format="json"
        )
        self.assertEqual(repeat.status_code, status.HTTP_400_BAD_REQUEST)

        detail = self.client.get(f"/api/games/{self.session.id}/").data
        self.assertEqual(detail["answered_count"], 1)
        self.assertEqual(detail["question_count"], 10)
        self.assertEqual(detail["max_xp"], 30)

    def test_refill_stores_explanations(self):
        with (
            patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key"),
            patch("apps.common.gemini.requests.post", return_value=_gemini_response(_questions_payload(3))),
        ):
            other_class = make_school_class(name="7-B")
            refill_pool(subject=self.subject, school_class=other_class, batch_size=3)

        self.assertEqual(
            sorted(PooledQuestion.objects.filter(school_class=other_class).values_list("explanation", flat=True)),
            ["Izoh 0", "Izoh 1", "Izoh 2"],
        )


class CodeBreakerTests(APITestCase):
    """Kodni buzish: a per-session secret code, one segment per correctly
    answered question, the full code only after an unlocked (>= 70%) finish,
    and XP awarded exactly once.
    """

    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        self.session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.CODE_BREAKER
        )
        pick_session_questions(self.session)

    def _play(self, correct_upto: int):
        for i, question in enumerate(self.session.questions):
            key = question["correct_index"]
            record_live_answer(
                session=self.session, question_index=i, selected_index=key if i < correct_upto else (key + 1) % 4
            )
        self.session.refresh_from_db()

    def test_each_session_gets_its_own_ten_character_code(self):
        other = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.CODE_BREAKER)
        self.assertEqual(len(self.session.secret_code), 10)
        self.assertNotEqual(self.session.secret_code, other.secret_code)

    def test_other_games_have_no_code(self):
        quiz = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        self.assertEqual(quiz.secret_code, "")
        self.assertEqual(revealed_code(quiz), [])

    def test_correct_answer_unlocks_only_its_own_segment(self):
        key = self.session.questions[0]["correct_index"]
        result = record_live_answer(session=self.session, question_index=0, selected_index=key)

        self.assertEqual(result["code_segment"], self.session.secret_code[0])
        self.session.refresh_from_db()
        self.assertEqual(revealed_code(self.session), [self.session.secret_code[0]] + [None] * 9)

    def test_wrong_answer_unlocks_nothing(self):
        key = self.session.questions[0]["correct_index"]
        result = record_live_answer(session=self.session, question_index=0, selected_index=(key + 1) % 4)

        self.assertIsNone(result["code_segment"])
        self.assertEqual(revealed_code(self.session), [None] * 10)

    def test_seventy_percent_unlocks_the_whole_code(self):
        self._play(correct_upto=7)
        session = submit_game(session=self.session, answers={0: 0})

        self.assertEqual(session.score_percent, 70.0)
        self.assertEqual(revealed_code(session), list(session.secret_code))

    def test_below_seventy_percent_keeps_unanswered_segments_locked(self):
        self._play(correct_upto=6)
        session = submit_game(session=self.session, answers={0: 0})

        code = revealed_code(session)
        self.assertEqual(code[:6], list(session.secret_code[:6]))
        self.assertEqual(code[6:], [None] * 4)

    def test_api_never_sends_the_full_code_before_unlocking(self):
        self.client.force_authenticate(self.student_user)
        detail = self.client.get(f"/api/games/{self.session.id}/").data

        self.assertNotIn("secret_code", detail)
        self.assertEqual(detail["revealed_code"], [None] * 10)
        self.assertIsNone(detail["review"])

    def test_locked_result_includes_review_with_explanations(self):
        self._play(correct_upto=5)
        self.client.force_authenticate(self.student_user)
        response = self.client.post(
            f"/api/games/{self.session.id}/submit/",
            {"answers": [{"question_index": 0, "selected_index": 0}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["goal_reached"])
        wrong = [r for r in response.data["review"] if r["selected_index"] != r["correct_index"]]
        self.assertEqual(len(wrong), 5)
        self.assertTrue(all(r["explanation"] for r in wrong))

    def test_xp_is_awarded_once_even_if_submit_is_repeated(self):
        self._play(correct_upto=10)
        self.client.force_authenticate(self.student_user)
        url = f"/api/games/{self.session.id}/submit/"
        payload = {"answers": [{"question_index": 0, "selected_index": 0}]}

        first = self.client.post(url, payload, format="json")
        second = self.client.post(url, payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(XPTransaction.objects.filter(student=self.student, source=XPTransaction.Source.GAME).count(), 1)
        self.assertEqual(first.data["xp_awarded"], 30)

    def test_a_stale_session_object_cannot_award_twice(self):
        """Two requests that loaded the session before either completed it."""
        self._play(correct_upto=10)
        stale = GameSession.objects.get(pk=self.session.pk)
        submit_game(session=self.session, answers={0: 0})

        with self.assertRaises(ValueError):
            submit_game(session=stale, answers={0: 0})
        self.assertEqual(XPTransaction.objects.filter(student=self.student, source=XPTransaction.Source.GAME).count(), 1)


class TreasureHuntTests(APITestCase):
    """Xazina ovi: same server-authoritative live-answer flow; the treasure is
    reached at 80% and only once the game is over."""

    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        self.session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.TREASURE_HUNT
        )
        pick_session_questions(self.session)

    def _play(self, correct_upto: int):
        for i, question in enumerate(self.session.questions):
            key = question["correct_index"]
            record_live_answer(
                session=self.session, question_index=i, selected_index=key if i < correct_upto else (key + 1) % 4
            )
        self.session.refresh_from_db()

    def _submit(self):
        self.client.force_authenticate(self.student_user)
        return self.client.post(
            f"/api/games/{self.session.id}/submit/",
            {"answers": [{"question_index": 0, "selected_index": 0}]},
            format="json",
        )

    def test_ten_questions_and_no_secret_code(self):
        self.assertEqual(len(self.session.questions), 10)
        self.assertEqual(self.session.secret_code, "")

    def test_answers_are_locked_in_like_the_other_live_games(self):
        self._play(correct_upto=3)
        with self.assertRaises(ValueError):
            record_live_answer(session=self.session, question_index=0, selected_index=0)

    def test_eighty_percent_reaches_the_treasure(self):
        self._play(correct_upto=8)
        response = self._submit()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["goal_reached"])
        self.assertEqual(response.data["unlock_percent"], 80)
        self.assertEqual(response.data["xp_awarded"], 24)

    def test_seventy_percent_completes_the_journey_without_the_treasure(self):
        self._play(correct_upto=7)
        response = self._submit()

        self.assertFalse(response.data["goal_reached"])
        self.assertEqual(response.data["correct_count"], 7)
        self.assertEqual(response.data["xp_awarded"], 21)

    def test_goal_is_never_reported_before_the_game_ends(self):
        self._play(correct_upto=10)
        self.client.force_authenticate(self.student_user)
        detail = self.client.get(f"/api/games/{self.session.id}/").data
        self.assertFalse(detail["goal_reached"])

    def test_xp_is_awarded_once(self):
        self._play(correct_upto=10)
        self.assertEqual(self._submit().status_code, status.HTTP_200_OK)
        self.assertEqual(self._submit().status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(XPTransaction.objects.filter(student=self.student, source=XPTransaction.Source.GAME).count(), 1)

    def test_other_games_have_no_win_threshold(self):
        quiz = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        self.client.force_authenticate(self.student_user)
        detail = self.client.get(f"/api/games/{quiz.id}/").data
        self.assertIsNone(detail["unlock_percent"])
        self.assertFalse(detail["goal_reached"])


class BattleArenaTests(APITestCase):
    """Jang maydoni: HP, combo and victory are replayed server-side from the
    recorded answers; a battle can end early and is scored over rounds fought."""

    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)
        self.session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.BATTLE_ARENA
        )
        pick_session_questions(self.session)

    def _answer(self, index, *, correct):
        key = self.session.questions[index]["correct_index"]
        return record_live_answer(
            session=self.session, question_index=index, selected_index=key if correct else (key + 1) % 4
        )

    def _submit(self):
        self.client.force_authenticate(self.student_user)
        return self.client.post(
            f"/api/games/{self.session.id}/submit/",
            {"answers": [{"question_index": 0, "selected_index": 0}]},
            format="json",
        )

    def test_correct_answer_damages_the_enemy_and_builds_combo(self):
        self._answer(0, correct=True)
        result = self._answer(1, correct=True)

        self.assertEqual(result["battle"]["enemy_hp"], 60)
        self.assertEqual(result["battle"]["player_hp"], 100)
        self.assertEqual(result["battle"]["combo"], 2)

    def test_wrong_answer_damages_the_player_and_resets_combo(self):
        self._answer(0, correct=True)
        result = self._answer(1, correct=False)

        self.assertEqual(result["battle"]["player_hp"], 90)
        self.assertEqual(result["battle"]["combo"], 0)
        self.assertEqual(result["battle"]["max_combo"], 1)

    def test_five_hits_win_early_and_no_more_answers_are_accepted(self):
        for i in range(5):
            result = self._answer(i, correct=True)

        self.assertTrue(result["battle"]["over"])
        self.assertTrue(result["battle"]["victory"])
        with self.assertRaises(ValueError):
            self._answer(5, correct=True)

    def test_running_xp_only_grows_with_hits(self):
        first = self._answer(0, correct=True)
        second = self._answer(1, correct=False)
        self.assertEqual(first["xp_earned"], 3)
        self.assertEqual(second["xp_earned"], 3)

    def test_early_victory_is_scored_over_rounds_fought_and_credits_the_rest(self):
        self._answer(0, correct=False)
        for i in range(1, 6):
            self._answer(i, correct=True)
        response = self._submit()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["goal_reached"])
        self.assertEqual(response.data["score_percent"], 83.33)
        # 5 hits + 4 rounds the knockout made unnecessary = 9/10 of 30 XP.
        self.assertEqual(response.data["xp_awarded"], 27)
        self.assertEqual(response.data["battle"]["rounds_played"], 6)

    def test_cannot_submit_while_the_battle_is_still_going(self):
        self._answer(0, correct=True)
        self.assertEqual(self._submit().status_code, status.HTTP_400_BAD_REQUEST)

    def test_all_rounds_without_a_knockout_ends_without_victory(self):
        for i in range(10):
            self._answer(i, correct=i < 4)
        response = self._submit()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["goal_reached"])
        self.assertEqual(response.data["xp_awarded"], 12)
        self.assertEqual(response.data["battle"]["enemy_hp"], 20)
        self.assertEqual(response.data["battle"]["player_hp"], 40)

    def test_xp_is_awarded_once(self):
        for i in range(5):
            self._answer(i, correct=True)
        self.assertEqual(self._submit().status_code, status.HTTP_200_OK)
        self.assertEqual(self._submit().status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(XPTransaction.objects.filter(student=self.student, source=XPTransaction.Source.GAME).count(), 1)

    def test_other_games_report_no_battle(self):
        quiz = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        self.client.force_authenticate(self.student_user)
        self.assertIsNone(self.client.get(f"/api/games/{quiz.id}/").data["battle"])


class TowerDefenseTests(APITestCase):
    """Tower Defense: difficulty sets the length and the fight; waves, enemy HP,
    shields, base HP, combo boosts and the outcome are all replayed server-side."""

    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)
        _seed_pool(subject=self.subject, school_class=self.school_class, count=20)

    def _start(self, difficulty="EASY"):
        session = start_game(
            student=self.student,
            subject=self.subject,
            game_type=GameSession.GameType.TOWER_DEFENSE,
            difficulty=difficulty,
        )
        pick_session_questions(session)
        return session

    def _answer(self, session, index, *, correct):
        key = session.questions[index]["correct_index"]
        return record_live_answer(
            session=session, question_index=index, selected_index=key if correct else (key + 1) % 4
        )

    def _submit(self, session):
        self.client.force_authenticate(self.student_user)
        return self.client.post(
            f"/api/games/{session.id}/submit/",
            {"answers": [{"question_index": 0, "selected_index": 0}]},
            format="json",
        )

    def test_difficulty_sets_the_number_of_questions_and_xp(self):
        for difficulty, count in (("EASY", 10), ("MEDIUM", 12), ("HARD", 14)):
            session = self._start(difficulty)
            self.assertEqual(len(session.questions), count)
            self.assertEqual(session.difficulty, difficulty)

    def test_other_games_ignore_difficulty(self):
        quiz = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ, difficulty="HARD"
        )
        self.assertEqual(quiz.difficulty, "")

    def test_a_hit_damages_the_front_enemy_and_a_miss_damages_the_base(self):
        session = self._start("EASY")
        hit = self._answer(session, 0, correct=True)["defense"]
        self.assertEqual(hit["last_event"]["kind"], "hit")
        self.assertTrue(hit["last_event"]["killed"])  # 40 damage vs a 25 HP scout
        self.assertEqual(hit["enemies_defeated"], 1)

        miss = self._answer(session, 1, correct=False)["defense"]
        self.assertEqual(miss["last_event"]["kind"], "base_hit")
        self.assertEqual(miss["base_hp"], 90)
        self.assertEqual(miss["combo"], 0)

    def test_shields_soak_damage_before_hp(self):
        session = self._start("EASY")
        self._answer(session, 0, correct=True)
        self._answer(session, 1, correct=True)  # wave 1 cleared → wave 2: one shielded enemy
        state = self._answer(session, 2, correct=True)["defense"]
        shielded = state["enemies"][0]
        self.assertEqual(shielded["type"], "shield")
        self.assertEqual(shielded["shield"], 0)
        self.assertEqual(shielded["hp"], 20)  # 40 damage: 20 into the shield, 20 into 40 HP
        self.assertTrue(state["last_event"]["shield_hit"])

    def test_a_combo_of_five_powers_up_the_tower(self):
        session = self._start("HARD")
        for i in range(5):
            state = self._answer(session, i, correct=True)["defense"]
        self.assertEqual(state["boost"], "POWER_BOOST")
        self.assertEqual(state["last_event"]["damage"], 66)  # 44 × 1.5

    def test_clearing_every_wave_is_a_victory_with_the_boss_last(self):
        session = self._start("EASY")
        seen_boss = False
        for i in range(10):
            state = self._answer(session, i, correct=True)["defense"]
            seen_boss = seen_boss or state["boss_wave"]
            if state["over"]:
                break
        self.assertTrue(state["victory"])
        self.assertTrue(seen_boss)
        with self.assertRaises(ValueError):
            self._answer(session, i + 1, correct=True)

        response = self._submit(session)
        self.assertTrue(response.data["goal_reached"])
        self.assertEqual(response.data["xp_awarded"], 30)  # 3 XP × 10 questions, unplayed rounds credited
        self.assertTrue(response.data["defense_record"]["is_record"])

    def test_a_fallen_base_ends_the_game_without_victory(self):
        session = self._start("HARD")
        for i in range(14):
            state = self._answer(session, i, correct=False)["defense"]
            if state["over"]:
                break
        self.assertEqual(state["base_hp"], 0)
        self.assertFalse(state["victory"])
        response = self._submit(session)
        self.assertFalse(response.data["goal_reached"])
        self.assertEqual(response.data["xp_awarded"], 0)

    def test_cannot_submit_mid_battle_and_xp_is_awarded_once(self):
        session = self._start("EASY")
        self._answer(session, 0, correct=True)
        self.assertEqual(self._submit(session).status_code, status.HTTP_400_BAD_REQUEST)
        for i in range(1, 10):
            if self._answer(session, i, correct=True)["defense"]["over"]:
                break
        self.assertEqual(self._submit(session).status_code, status.HTTP_200_OK)
        self.assertEqual(self._submit(session).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            XPTransaction.objects.filter(student=self.student, source=XPTransaction.Source.GAME).count(), 1
        )

    def test_personal_record_compares_with_earlier_games(self):
        first = self._start("EASY")
        for i in range(10):
            if self._answer(first, i, correct=True)["defense"]["over"]:
                break
        self._submit(first)

        second = self._start("EASY")
        for i in range(10):
            if self._answer(second, i, correct=i % 2 == 0)["defense"]["over"]:
                break
        record = self._submit(second).data["defense_record"]
        self.assertIsNotNone(record["best_before"])
        self.assertFalse(record["is_record"])

    def test_api_accepts_a_difficulty(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.post(
            "/api/games/",
            {"subject": self.subject.id, "game_type": "TOWER_DEFENSE", "difficulty": "HARD"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["difficulty"], "HARD")
        self.assertEqual(response.data["question_count"], 14)
        self.assertEqual(response.data["max_xp"], 42)
        self.assertEqual(response.data["defense"]["waves_total"], 4)
