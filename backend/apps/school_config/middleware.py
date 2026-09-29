from django.http import JsonResponse
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import SchoolTimeSettings

# The whole /api/auth/ namespace stays reachable during the lock, not just login
# and refresh: it holds only identity and session lifecycle (login, refresh, me,
# change-password, avatar), never the learning content the lock is meant to gate.
# Locking /api/auth/me/ would leave the app unable to tell who is signed in, and
# locking change-password would permanently trap any student who was issued a
# temporary password (e.g. by the bulk import) in a 423 loop.
EXEMPT_PATH_PREFIXES = (
    "/api/auth/",
    "/api/schema",
    "/api/docs",
    "/api/redoc",
)


class SchoolTimeLockMiddleware:
    """Blocks STUDENT accounts from using the web API during school hours.

    Runs as plain Django middleware (not a DRF permission) so every current and
    future API view is covered automatically, with no per-view wiring required.
    Director and Teacher accounts are never affected.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()

    def __call__(self, request):
        if self._is_locked_out(request):
            settings_obj = SchoolTimeSettings.get_solo()
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

        settings_obj = SchoolTimeSettings.get_solo()
        return settings_obj.is_locked_at(timezone.localtime().time())

    def _authenticate(self, request):
        try:
            result = self.jwt_authenticator.authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None
        return result[0] if result else None
