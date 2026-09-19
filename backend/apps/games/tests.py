import json
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import make_school_class, make_student, make_subject, make_teacher
from apps.gamification.models import XPTransaction

from .models import GameSession
from .services import generate_questions, start_game, submit_game


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


class GameServiceTests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        self.school_class = make_school_class()
        self.student_user, self.student = make_student(self.school_class)

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key")
    @patch("apps.common.gemini.requests.post")
    def test_generate_questions_caps_at_eight(self, mock_post):
        session = start_game(student=self.student, subject=self.subject, game_type=GameSession.GameType.QUIZ)
        mock_post.return_value = _gemini_response(_questions_payload(12))
        questions = generate_questions(session)
        self.assertEqual(len(questions), 8)

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key")
    @patch("apps.common.gemini.requests.post")
    def test_submit_scores_and_awards_xp(self, mock_post):
        session = start_game(
            student=self.student, subject=self.subject, game_type=GameSession.GameType.TUG_OF_WAR
        )
        mock_post.return_value = _gemini_response(_questions_payload(4))
        generate_questions(session)

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

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "test-key")
    @patch("apps.common.gemini.requests.post")
    def test_full_flow_via_api(self, mock_post):
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            "/api/games/", {"subject": self.subject.id, "game_type": "QUIZ"}, format="json"
        )
        session_id = create_response.data["id"]

        mock_post.return_value = _gemini_response(_questions_payload(8))
        questions_response = self.client.get(f"/api/games/{session_id}/questions/")
        self.assertEqual(questions_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(questions_response.data), 8)
        self.assertNotIn("correct_index", questions_response.data[0])

        answers = [{"question_index": i, "selected_index": 0} for i in range(8)]
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
