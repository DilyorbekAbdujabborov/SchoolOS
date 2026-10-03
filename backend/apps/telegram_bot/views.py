import json
import logging
import secrets

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .bot import enqueue_update
from .models import TelegramAccount
from .serializers import TelegramLinkCodeSerializer, TelegramStatusSerializer

logger = logging.getLogger(__name__)


class TelegramLinkCodeView(APIView):
    """Issue a fresh one-time code the user types into the bot as `/start <code>`."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        link_code = services.generate_link_code(request.user)
        return Response(TelegramLinkCodeSerializer(link_code).data)


class TelegramStatusView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        account = TelegramAccount.objects.filter(user=request.user).first()
        data = {
            "linked": account is not None,
            "telegram_username": account.telegram_username if account else None,
        }
        return Response(TelegramStatusSerializer(data).data)


class TelegramUnlinkView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        TelegramAccount.objects.filter(user=request.user).delete()
        return Response(status=204)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """Telegram's delivery endpoint for updates (registered by
    `manage.py telegram_webhook set`).

    A plain Django view rather than a DRF `APIView` on purpose: this is not part of
    the JWT API the frontend uses, and keeping it out of DRF also keeps it out of
    the OpenAPI schema. `csrf_exempt` is required because Telegram can't send a
    CSRF token, and the request is authorised by the shared secret header Telegram
    echoes back on every call instead.
    """

    secret_header = "HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN"

    def post(self, request):
        expected_secret = settings.TELEGRAM_WEBHOOK_SECRET
        if not expected_secret:
            logger.error(
                "TELEGRAM_WEBHOOK_SECRET is not set — rejecting Telegram update."
            )
            return JsonResponse(
                {"detail": "Webhook is not configured on the server."}, status=503
            )

        provided_secret = request.META.get(self.secret_header, "")
        if not secrets.compare_digest(provided_secret, expected_secret):
            return JsonResponse({"detail": "Invalid secret token."}, status=403)

        try:
            update_data = json.loads(request.body)
        except ValueError:
            return JsonResponse({"detail": "Malformed JSON body."}, status=400)

        if not isinstance(update_data, dict):
            return JsonResponse({"detail": "Malformed JSON body."}, status=400)

        try:
            # Returns as soon as the update is queued on the bot's event loop.
            enqueue_update(update_data)
        except Exception:
            logger.exception("Could not start the Telegram bot to handle an update.")
            return JsonResponse({"detail": "Telegram bot is unavailable."}, status=503)

        return JsonResponse({"ok": True})


# --- Parent Telegram Accounts ---

class ParentTelegramAccountsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        accounts = TelegramAccount.objects.filter(user=request.user).order_by("-created_at")
        return Response([
            {
                "id": a.id,
                "telegram_username": a.telegram_username,
                "created_at": a.created_at.isoformat(),
            }
            for a in accounts
        ])

    def delete(self, request):
        account_id = request.query_params.get("id")
        if not account_id:
            return Response({"detail": "id required"}, status=400)
        deleted, _ = TelegramAccount.objects.filter(user=request.user, id=account_id).delete()
        if not deleted:
            return Response({"detail": "Not found"}, status=404)
        return Response(status=204)
