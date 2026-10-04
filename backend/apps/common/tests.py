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
        # The key travels in a header, never in the URL (which ends up in logs).
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], "gemini-key")
        self.assertNotIn("gemini-key", args[0])
        self.assertNotIn("params", kwargs)

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


class ShuffleOptionsTests(TestCase):
    def test_keeps_the_right_answer_and_every_option(self):
        from apps.common.questions import shuffle_options

        question = {"text": "2+2?", "options": ["4", "3", "5", "22"], "correct_index": 0, "explanation": "x"}
        for _ in range(20):
            shuffled = shuffle_options(question)
            self.assertEqual(shuffled["options"][shuffled["correct_index"]], "4")
            self.assertEqual(sorted(shuffled["options"]), sorted(question["options"]))
            self.assertEqual(shuffled["explanation"], "x")
        self.assertEqual(question["options"], ["4", "3", "5", "22"])  # input untouched

    def test_the_answer_does_not_stay_in_one_slot(self):
        from apps.common.questions import shuffle_options

        question = {"text": "2+2?", "options": ["4", "3", "5", "22"], "correct_index": 0}
        slots = {shuffle_options(question)["correct_index"] for _ in range(60)}
        self.assertGreater(len(slots), 1)


class ExceptionEnvelopeTests(TestCase):
    """The custom handler normalises every DRF error into one envelope:
    {error_code, detail, errors}. HTTP status is never duplicated into the body.
    """

    def _handle(self, exc):
        from .exceptions import custom_exception_handler

        response = custom_exception_handler(exc, {})
        return response

    def test_plain_detail_exception(self):
        from rest_framework.exceptions import PermissionDenied

        data = self._handle(PermissionDenied("Ruxsat yo'q")).data
        self.assertEqual(data["error_code"], "permission_denied")
        self.assertEqual(data["detail"], "Ruxsat yo'q")
        self.assertIsNone(data["errors"])

    def test_validation_error_from_a_string_is_flattened(self):
        from rest_framework.exceptions import ValidationError

        # ValidationError("msg") renders as a bare list ["msg"] by default.
        data = self._handle(ValidationError("Savol yetarli emas")).data
        self.assertEqual(data["error_code"], "invalid")
        self.assertEqual(data["detail"], "Savol yetarli emas")
        self.assertIsNone(data["errors"])

    def test_field_errors_are_kept_and_headlined(self):
        from rest_framework.exceptions import ValidationError

        data = self._handle(ValidationError({"end_time": ["Boshlanishdan keyin bo'lsin"]})).data
        self.assertEqual(data["error_code"], "invalid")
        self.assertEqual(data["detail"], "Boshlanishdan keyin bo'lsin")
        self.assertEqual(data["errors"], {"end_time": ["Boshlanishdan keyin bo'lsin"]})

    def test_non_field_errors_lead_the_headline(self):
        from rest_framework.exceptions import ValidationError

        data = self._handle(
            ValidationError({"name": ["x"], "non_field_errors": ["Umumiy xato"]})
        ).data
        self.assertEqual(data["detail"], "Umumiy xato")
        self.assertIn("name", data["errors"])

    def test_app_error_carries_its_code(self):
        from rest_framework import status

        from .exceptions import AppError

        class InsufficientXP(AppError):
            status_code = status.HTTP_409_CONFLICT
            default_detail = "XP yetarli emas."
            default_code = "insufficient_xp"

        response = self._handle(InsufficientXP())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error_code"], "insufficient_xp")
        self.assertEqual(response.data["detail"], "XP yetarli emas.")

    def test_unhandled_exception_is_left_for_django(self):
        # A non-DRF exception returns None → Django renders its own 500.
        self.assertIsNone(self._handle(KeyError("boom")))
