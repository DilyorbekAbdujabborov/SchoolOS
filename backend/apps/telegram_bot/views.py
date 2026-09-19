from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsStudent

from . import services
from .models import ParentTelegramAccount, TelegramAccount
from .serializers import (
    ParentLinkCodeSerializer,
    ParentTelegramAccountSerializer,
    TelegramLinkCodeSerializer,
    TelegramStatusSerializer,
)


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


class ParentLinkCodeView(APIView):
    """Issue a fresh one-time code the student shares with their parent, who
    types it into the bot as `/start <code>` to link their own Telegram chat."""

    permission_classes = (IsStudent,)

    def post(self, request):
        link_code = services.generate_parent_link_code(request.user.student_profile)
        return Response(ParentLinkCodeSerializer(link_code).data)


class ParentTelegramAccountsView(APIView):
    """Lists (and lets the student unlink) the parent chats linked to them."""

    permission_classes = (IsStudent,)

    def get(self, request):
        accounts = ParentTelegramAccount.objects.filter(student=request.user.student_profile)
        return Response(ParentTelegramAccountSerializer(accounts, many=True).data)

    def delete(self, request, pk):
        account = ParentTelegramAccount.objects.filter(
            student=request.user.student_profile, pk=pk
        ).first()
        if account is None:
            raise NotFound("Parent Telegram account not found.")
        account.delete()
        return Response(status=204)
