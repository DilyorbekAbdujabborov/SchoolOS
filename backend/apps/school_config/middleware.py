from django.http import JsonResponse
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

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
        if self._is_locked_out(request):
            settings_obj = self._get_settings(request)
            return JsonResponse(
                {
                    "detail": (
                        "Iltimos, darsga qatnashing. Platformadan foydalanish "
                        f"soat {settings_obj.end_time:%H:%M} dan keyin ochiladi."
                    )
                },
                status=423,
            )
        return self.get_response(request)

    def _is_locked_out(self, request) -> bool:
        if not request.path.startswith("/api/"):
            return False
        if request.path.startswith(EXEMPT_PATH_PREFIXES):
            return False

        user = self._authenticate(request)
        if user is None or not user.is_authenticated or not user.is_student:
            return False

        settings_obj = self._get_settings_for_user(user)
        if not settings_obj:
            return False
        return settings_obj.is_locked_at(timezone.localtime().time())

    def _get_settings(self, request):
        user = self._authenticate(request)
        if user and user.is_authenticated:
            return self._get_settings_for_user(user)
        return SchoolTimeSettings.objects.first()

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
