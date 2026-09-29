import asyncio

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Update

from apps.telegram_bot.bot import build_application


class Command(BaseCommand):
    help = "Run the SchoolOS Telegram bot (long polling) — local development only."

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stderr.write("TELEGRAM_BOT_TOKEN is not set — add it to your .env first.")
            return

        # Python 3.12+ no longer lets asyncio.get_event_loop() create one implicitly,
        # which is what Application.run_polling() relies on internally.
        asyncio.set_event_loop(asyncio.new_event_loop())

        application = build_application(token)

        self.stdout.write(self.style.SUCCESS("SchoolOS Telegram bot started (polling)..."))
        # Production serves updates through the webhook instead. Once a webhook is
        # registered Telegram answers getUpdates with 409, so this would only spam
        # errors — run `manage.py telegram_webhook delete` before polling again.
        application.run_polling(allowed_updates=Update.ALL_TYPES)
