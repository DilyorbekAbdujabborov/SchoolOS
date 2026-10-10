"""What an organization may do — the client-config capability registry.

A capability key is `<resource>.<action>`. The platform owner stores a *deny*
list per organization (`ClientConfig.denied`); anything not denied is allowed, so
a resource added here later is automatically open for every existing school.
Denying `<resource>.read` closes the whole resource (it disappears from the
sidebar, and nothing invisible can be edited).

This registry is the single source of truth: enforcement maps an API path to a
resource through `api_prefixes`, and the frontend uses the same keys.
"""

from dataclasses import dataclass

ACTIONS = ("read", "create", "update", "delete")

_METHOD_ACTION = {
    "GET": "read",
    "HEAD": "read",
    "OPTIONS": "read",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


@dataclass(frozen=True)
class Resource:
    label: str
    #: First path segment(s) after `/api/`, matched as whole segments.
    api_prefixes: tuple[str, ...]


RESOURCES: dict[str, Resource] = {
    "students": Resource("O'quvchilar", ("students",)),
    "teachers": Resource("O'qituvchilar", ("teachers",)),
    "classes": Resource("Sinflar", ("classes",)),
    "subjects": Resource("Fanlar", ("subjects",)),
    "timetable": Resource("Dars jadvali", ("timetable", "timetable-slots", "lessons")),
    "attendance": Resource("Davomat", ("attendance",)),
    "materials": Resource("Materiallar", ("materials",)),
    "tests": Resource(
        "Testlar",
        ("tests", "questions", "options", "my-attempts"),
    ),
    "activities": Resource(
        "Topshiriqlar", ("activities", "activity-submissions", "my-activity-submissions")
    ),
    "tasks": Resource("Vazifalar", ("teacher-tasks", "my-tasks")),
    "games": Resource("O'yinlar", ("games", "question-pools")),
    "duels": Resource("Duellar", ("duels",)),
    "gamification": Resource(
        "Gamifikatsiya",
        ("xp", "streaks", "achievements", "leaderboard", "league", "weekly-goal"),
    ),
    "remedial": Resource("Qo'shimcha darslar", ("remedial-sessions",)),
    "reports": Resource("Hisobotlar", ("reports", "dashboard")),
}

_PREFIX_RESOURCE = {
    prefix: key for key, resource in RESOURCES.items() for prefix in resource.api_prefixes
}


def all_keys() -> list[str]:
    return [f"{resource}.{action}" for resource in RESOURCES for action in ACTIONS]


def capability_for(path: str, method: str) -> str | None:
    """The capability key a request needs, or None when the path is never gated."""
    if not path.startswith("/api/"):
        return None
    segment = path[len("/api/"):].split("/", 1)[0]
    resource = _PREFIX_RESOURCE.get(segment)
    action = _METHOD_ACTION.get(method.upper())
    if resource is None or action is None:
        return None
    return f"{resource}.{action}"


def is_allowed(denied: frozenset[str], key: str) -> bool:
    resource, _sep, _action = key.partition(".")
    return key not in denied and f"{resource}.read" not in denied


def get_denied(organization) -> frozenset[str]:
    """Denied keys for `organization`; empty when it has no config row."""
    from .models import ClientConfig

    denied = (
        ClientConfig.objects.filter(organization=organization)
        .values_list("denied", flat=True)
        .first()
    )
    return frozenset(denied or ())
