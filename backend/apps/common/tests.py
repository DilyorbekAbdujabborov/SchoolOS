from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .gemini import call_gemini
from .permissions import IsDirector, IsDirectorOrReadOnly, IsStudent, IsTeacher
from .testing import make_director, make_student, make_teacher


class RolePermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.director = make_director()
        self.teacher_user, _ = make_teacher()
        self.student_user, _ = make_student()

    def _request(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_is_director_allows_only_director(self):
        permission = IsDirector()
        self.assertTrue(permission.has_permission(self._request(self.director), None))
        self.assertFalse(permission.has_permission(self._request(self.teacher_user), None))
        self.assertFalse(permission.has_permission(self._request(self.student_user), None))

    def test_is_teacher_allows_only_teacher(self):
        permission = IsTeacher()
        self.assertFalse(permission.has_permission(self._request(self.director), None))
        self.assertTrue(permission.has_permission(self._request(self.teacher_user), None))
        self.assertFalse(permission.has_permission(self._request(self.student_user), None))

    def test_is_student_allows_only_student(self):
        permission = IsStudent()
        self.assertFalse(permission.has_permission(self._request(self.director), None))
        self.assertFalse(permission.has_permission(self._request(self.teacher_user), None))
        self.assertTrue(permission.has_permission(self._request(self.student_user), None))

    def test_is_director_or_read_only(self):
        permission = IsDirectorOrReadOnly()

        get_request = self.factory.get("/")
        get_request.user = self.teacher_user
        self.assertTrue(permission.has_permission(get_request, None))

        post_request = self.factory.post("/")
        post_request.user = self.teacher_user
        self.assertFalse(permission.has_permission(post_request, None))

        director_post = self.factory.post("/")
        director_post.user = self.director
        self.assertTrue(permission.has_permission(director_post, None))


def _gemini_ok(content: str) -> Mock:
    response = Mock(status_code=200)
    response.raise_for_status = Mock()
    response.json.return_value = {"candidates": [{"content": {"parts": [{"text": content}]}}]}
    return response


def _gemini_rate_limited() -> Mock:
    return Mock(status_code=429)


def _groq_ok(content: str) -> Mock:
    response = Mock(status_code=200)
    response.raise_for_status = Mock()
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


class GeminiGroqFallbackTests(TestCase):
    """Gemini is the primary AI provider; Groq is an automatic fallback so a
    quota-exhausted or misconfigured Gemini key never takes an AI feature
    fully offline."""

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "gemini-key")
    @patch("apps.common.gemini.settings.GROQ_API_KEY", "groq-key")
    @patch("apps.common.gemini.requests.post")
    def test_uses_gemini_when_it_succeeds(self, mock_post):
        mock_post.return_value = _gemini_ok("gemini natija")

        result = call_gemini(prompt="salom")

        self.assertEqual(result, "gemini natija")
        mock_post.assert_called_once()

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "gemini-key")
    @patch("apps.common.gemini.settings.GROQ_API_KEY", "groq-key")
    @patch("apps.common.gemini.requests.post")
    def test_falls_back_to_groq_when_gemini_is_rate_limited(self, mock_post):
        mock_post.side_effect = [_gemini_rate_limited(), _groq_ok("groq natija")]

        result = call_gemini(prompt="salom")

        self.assertEqual(result, "groq natija")
        self.assertEqual(mock_post.call_count, 2)

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "")
    @patch("apps.common.gemini.settings.GROQ_API_KEY", "groq-key")
    @patch("apps.common.gemini.requests.post")
    def test_falls_back_to_groq_when_gemini_has_no_key(self, mock_post):
        mock_post.return_value = _groq_ok("groq natija")

        result = call_gemini(prompt="salom")

        self.assertEqual(result, "groq natija")
        mock_post.assert_called_once()

    @patch("apps.common.gemini.settings.GEMINI_API_KEY", "")
    @patch("apps.common.gemini.settings.GROQ_API_KEY", "")
    def test_returns_none_when_neither_provider_is_configured(self):
        self.assertIsNone(call_gemini(prompt="salom"))
