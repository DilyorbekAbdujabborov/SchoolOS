from django.urls import path

from .views import (
    ParentLinkCodeView,
    ParentTelegramAccountsView,
    TelegramLinkCodeView,
    TelegramStatusView,
    TelegramUnlinkView,
)

urlpatterns = [
    path("telegram/link-code/", TelegramLinkCodeView.as_view(), name="telegram-link-code"),
    path("telegram/status/", TelegramStatusView.as_view(), name="telegram-status"),
    path("telegram/unlink/", TelegramUnlinkView.as_view(), name="telegram-unlink"),
    path(
        "telegram/parent-link-code/", ParentLinkCodeView.as_view(), name="telegram-parent-link-code"
    ),
    path(
        "telegram/parent-accounts/",
        ParentTelegramAccountsView.as_view(),
        name="telegram-parent-accounts",
    ),
    path(
        "telegram/parent-accounts/<int:pk>/",
        ParentTelegramAccountsView.as_view(),
        name="telegram-parent-account-detail",
    ),
]
