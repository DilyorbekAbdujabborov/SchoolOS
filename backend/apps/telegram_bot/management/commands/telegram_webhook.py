"""Register / inspect / remove the Telegram webhook.

Production delivers updates by webhook; `runbot` (long polling) is for local
development. Telegram only allows one of the two at a time — registering a
webhook while polling is active, or polling while a webhook is set, fails with
409 — so use `delete` before switching back to `runbot`.
"""

import asyncio

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram import Bot, Update
from telegram.error import TelegramError

_SECRET_HINT = (
    'add one with: python -c "import secrets; print(secrets.token_hex(32))"'
)


class Command(BaseCommand):
    help = "Manage the Telegram webhook: set, delete or info."

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["set", "delete", "info"],
            help=(
                "set: register TELEGRAM_WEBHOOK_URL with Telegram. "
                "delete: remove it (goes back to long polling). "
                "info: show what Telegram currently has registered."
            ),
        )
        parser.add_argument(
            "--drop-pending",
            action="store_true",
            help="Discard updates Telegram queued before the webhook was registered.",
        )

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set — add it to your .env first.")

        action = options["action"]
        drop_pending = options["drop_pending"]

        url = None
        secret = None
        if action == "set":
            url = settings.TELEGRAM_WEBHOOK_URL
            if not url:
                raise CommandError("TELEGRAM_WEBHOOK_URL is not set — add it to your .env first.")
            secret = settings.TELEGRAM_WEBHOOK_SECRET
            if not secret:
                raise CommandError(f"TELEGRAM_WEBHOOK_SECRET is not set — {_SECRET_HINT}")

        async def run() -> str:
            bot = Bot(token=token)
            try:
                if action == "set":
                    registered = await bot.set_webhook(
                        url=url,
                        secret_token=secret,
                        allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=drop_pending,
                    )
                    if not registered:
                        raise CommandError(
                            "Telegram rejected the webhook. Check that "
                            "TELEGRAM_WEBHOOK_URL is a public HTTPS endpoint "
                            "serving a valid certificate."
                        )
                    self.stdout.write(self.style.SUCCESS(f"Webhook registered: {url}"))
                elif action == "delete":
                    await bot.delete_webhook(drop_pending_updates=drop_pending)
                    self.stdout.write(self.style.SUCCESS("Webhook deleted — long polling is available again."))

                info = await bot.get_webhook_info()
                return (
                    f"\nurl:                    {info.url or '(none)'}\n"
                    f"pending update count:   {info.pending_update_count}\n"
                    f"last error message:     {info.last_error_message or '(none)'}"
                )
            except TelegramError as exc:
                raise CommandError(f"Telegram API error: {exc}") from exc
            finally:
                await bot.shutdown()

        self.stdout.write(asyncio.run(run()))
