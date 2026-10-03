from .models import Notification


def notify(
    *, recipient, title: str, body: str, category: str = Notification.Category.GENERAL
) -> Notification:
    """Create a web notification for `recipient`, then fan it out to Telegram and Web Push.

    This stays the single entry point every feature calls to notify a user,
    regardless of channel — callers never need to know which channels are wired up.
    Each side channel is best-effort: a failure there never stops the DB row from
    being created or the other channels from firing.
    """
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        body=body,
        category=category,
    )

    from apps.telegram_bot.services import notify_telegram

    notify_telegram(recipient, f"🔔 {title}\n\n{body}")

    from .push import send_web_push

    send_web_push(recipient, title, body)

    return notification
