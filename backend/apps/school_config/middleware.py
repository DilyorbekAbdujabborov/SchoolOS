from django.http import JsonResponse
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from . import services
from .models import SchoolTimeSettings

EXEMPT_PATH_PREFIXES = (
    "/api/auth/",
    "/api/schema",
    "/api/docs",
    "/api/redoc",
)


class SchoolTimeLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()

    def __call__(self, request):
        locked_response = self._locked_response(request)
        if locked_response is not None:
            return locked_response
        return self.get_response(request)

    def _locked_response(self, request):
        """The 423 to return, or None if this request may pass.

        Authentication is decoded exactly once here — the settings lookup and
        the message both reuse that same user, so a locked request never pays
        for the JWT twice.
        """
        if not request.path.startswith("/api/"):
            return None
        if request.path.startswith(EXEMPT_PATH_PREFIXES):
            return None

        user = self._authenticate(request)
        if user is None or not user.is_authenticated or not user.is_student:
            return None

        settings_obj = self._get_settings_for_user(user)
        if not settings_obj:
            return None
        now_local = timezone.localtime()
        # Weekends / days off are never locked — only school days, during hours.
        if not settings_obj.is_school_day(now_local.date()):
            return None
        if not settings_obj.is_locked_at(now_local.time()):
            return None

        # A teacher may have opened the platform for this student's class during
        # a lesson — that lifts the time lock until the window expires.
        profile = getattr(user, "student_profile", None)
        if profile and services.class_is_open(profile.school_class_id):
            return None

        return JsonResponse(
            {
                "detail": (
                    "Iltimos, darsga qatnashing. Platformadan foydalanish "
                    f"soat {settings_obj.end_time:%H:%M} dan keyin ochiladi."
                )
            },
            status=423,
        )

    def _get_settings_for_user(self, user):
        if hasattr(user, 'active_organization_id') and user.active_organization_id:
            try:
                return SchoolTimeSettings.objects.get(organization_id=user.active_organization_id)
            except SchoolTimeSettings.DoesNotExist:
                pass
        return SchoolTimeSettings.objects.first()

    def _authenticate(self, request):
        try:
            result = self.jwt_authenticator.authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None
        return result[0] if result else None
