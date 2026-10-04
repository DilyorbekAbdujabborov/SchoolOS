"""A uniform error envelope for every API error response.

DRF, out of the box, renders errors in several shapes: ``{"detail": "..."}``
for a plain ``APIException``, a bare list ``["..."]`` for
``ValidationError("msg")``, and ``{"field": ["..."]}`` for serializer
validation. The frontend only ever read ``response.data.detail``, so the
list/field-shaped messages never surfaced.

``custom_exception_handler`` normalises all of them into one shape::

    {
      "error_code": "invalid",        # machine-readable, from the exception
      "detail": "XP yetarli emas",    # one human-readable message (always present)
      "errors": {"amount": ["..."]}   # field-level errors, or null
    }

HTTP status is deliberately NOT duplicated into the body — the response's own
status code is the single source of truth. Success responses are untouched:
this only runs for exceptions DRF already turns into a 4xx/5xx.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class AppError(APIException):
    """Base for domain errors that want an explicit, stable ``error_code``.

    Prefer this over a bare ``ValueError`` in the service layer when the
    frontend needs to branch on the specific error (e.g. show a tailored
    message or action), rather than just display ``detail``::

        class InsufficientXP(AppError):
            status_code = status.HTTP_409_CONFLICT
            default_detail = "XP yetarli emas."
            default_code = "insufficient_xp"
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Xatolik yuz berdi."
    default_code = "error"


def _flatten(data: Any) -> tuple[str, dict[str, list[str]] | None]:
    """Reduce a DRF error body to (one human message, field errors | None)."""
    if isinstance(data, dict):
        # A plain {"detail": "..."} (APIException) — no field errors.
        if set(data.keys()) == {"detail"}:
            return str(data["detail"]), None
        # Serializer-style {field: [msgs], ...} (may also carry a "detail").
        errors: dict[str, list[str]] = {}
        for key, value in data.items():
            if isinstance(value, list):
                errors[key] = [str(v) for v in value]
            else:
                errors[key] = [str(value)]
        detail = _first_message(errors) or str(data.get("detail", "Xatolik yuz berdi."))
        return detail, errors
    if isinstance(data, list):
        return (str(data[0]) if data else "Xatolik yuz berdi."), None
    return str(data), None


def _first_message(errors: dict[str, list[str]]) -> str | None:
    # Prefer a non-field error for the headline message, else the first field's.
    for key in ("non_field_errors", "detail"):
        if errors.get(key):
            return errors[key][0]
    for messages in errors.values():
        if messages:
            return messages[0]
    return None


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    # None means DRF didn't handle it (e.g. an unexpected 500) — leave it be.
    if response is None:
        return response

    detail, errors = _flatten(response.data)
    code = getattr(exc, "default_code", None) or exc.__class__.__name__

    response.data = {
        "error_code": str(code),
        "detail": detail,
        "errors": errors,
    }
    return response
