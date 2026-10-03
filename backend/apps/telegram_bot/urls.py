from django.urls import path

from .views import (
    ParentTelegramAccountsView,
    TelegramLinkCodeView,
    TelegramStatusView,
    TelegramUnlinkView,
    TelegramWebhookView,
)

urlpatterns = [
    path("telegram/parent-link-code/", TelegramLinkCodeView.as_view(), name="telegram-parent-link-code"),
    path("telegram/parent-accounts/", ParentTelegramAccountsView.as_view(), name="telegram-parent-accounts"),
    path("telegram/link-code/", TelegramLinkCodeView.as_view(), name="telegram-link-code"),
    path("telegram/status/", TelegramStatusView.as_view(), name="telegram-status"),
    path("telegram/unlink/", TelegramUnlinkView.as_view(), name="telegram-unlink"),
    # Telegram's own delivery endpoint — not part of the JWT API, no auth beyond
    # the shared secret header, so it is kept out of the OpenAPI schema.
    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
]
