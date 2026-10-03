"""Web Push delivery: the browser-notification channel behind `notify()`.

Sending is a best-effort side channel. If no VAPID keys are configured, or the
`pywebpush` dependency is missing, `send_web_push` is a silent no-op so the core
notification (the DB row and the Telegram message) is never held hostage to the
push setup. Endpoints the push service reports as gone (404/410) are pruned.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_web_push(user, title: str, body: str, url: str = "/") -> None:
    """Fan `title`/`body` out to every Web Push subscription `user` has.

    Safe to call unconditionally: returns early when push is not configured, and
    swallows per-endpoint failures so one dead browser can't break the rest.
    """
    private_key = getattr(settings, "VAPID_PRIVATE_KEY", "")
    if not private_key:
        return

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush not installed; skipping web push")
        return

    from .models import PushSubscription

    subscriptions = list(PushSubscription.objects.filter(user=user))
    if not subscriptions:
        return

    payload = json.dumps({"title": title, "body": body, "url": url})
    admin_email = getattr(settings, "VAPID_ADMIN_EMAIL", "") or "admin@example.com"
    vapid_claims = {"sub": f"mailto:{admin_email}"}

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=dict(vapid_claims),
            )
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (404, 410):
                # Endpoint is permanently gone; drop it so it isn't retried.
                subscription.delete()
            else:
                logger.warning("Web push failed for user %s: %s", user.pk, exc)
        except Exception:
            # A broad catch is deliberate: push is best-effort and must never
            # break the caller, whatever pywebpush or the transport throws.
            logger.exception("Unexpected web push error for user %s", user.pk)
