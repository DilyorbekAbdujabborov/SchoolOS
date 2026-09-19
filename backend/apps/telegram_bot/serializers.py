from django.conf import settings
from rest_framework import serializers

from .models import ParentLinkCode, ParentTelegramAccount, TelegramLinkCode


class TelegramLinkCodeSerializer(serializers.ModelSerializer):
    bot_username = serializers.SerializerMethodField()

    class Meta:
        model = TelegramLinkCode
        fields = ("code", "expires_at", "bot_username")

    def get_bot_username(self, obj) -> str:
        return settings.TELEGRAM_BOT_USERNAME


class TelegramStatusSerializer(serializers.Serializer):
    linked = serializers.BooleanField()
    telegram_username = serializers.CharField(allow_null=True)


class ParentLinkCodeSerializer(serializers.ModelSerializer):
    bot_username = serializers.SerializerMethodField()

    class Meta:
        model = ParentLinkCode
        fields = ("code", "expires_at", "bot_username")

    def get_bot_username(self, obj) -> str:
        return settings.TELEGRAM_BOT_USERNAME


class ParentTelegramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentTelegramAccount
        fields = ("id", "telegram_username", "created_at")
