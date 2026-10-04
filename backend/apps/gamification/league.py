"""Weekly leagues and the weekly XP goal — the gamification "Liga" page.

Students are placed in a tier (Bronza … Afsona). Within a tier they are ranked
by the XP they earn *this week*, which resets every Monday. At the Monday roll-up
the top slice of each tier is promoted and the bottom slice relegated, and each
student's weekly-goal streak is updated. Ranking is always computed live from
`XPTransaction`, so the board is real-time; only the tier and the goal streak
persist (see models.py).
"""

from collections import defaultdict
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from apps.organizations.models import Organization
from apps.users.models import StudentProfile

from .models import LeagueCycle, LeagueStanding, WeeklyGoal, XPTransaction

#: (tier number, display name, emoji). Lowest to highest. The numbers are what
#: `LeagueStanding.tier` stores; names/icons live here so the model stays plain.
LEAGUE_TIERS: list[tuple[int, str, str]] = [
    (1, "Bronza liga", "🥉"),
    (2, "Kumush liga", "🥈"),
    (3, "Oltin liga", "🥇"),
    (4, "Olmos liga", "💎"),
    (5, "Brilliant liga", "✨"),
    (6, "Usta liga", "🎖️"),
    (7, "Grandmaster liga", "🏆"),
    (8, "Chempion liga", "👑"),
    (9, "Afsona liga", "🔥"),
]
MIN_TIER = LEAGUE_TIERS[0][0]
MAX_TIER = LEAGUE_TIERS[-1][0]
_TIER_META = {number: (name, icon) for number, name, icon in LEAGUE_TIERS}

#: Fraction of each tier promoted up and relegated down every week.
PROMOTE_FRACTION = 0.2
DEFAULT_WEEKLY_GOAL = 500


def tier_name(tier: int) -> str:
    return _TIER_META.get(tier, (f"Liga {tier}", ""))[0]


def tier_icon(tier: int) -> str:
    return _TIER_META.get(tier, ("", ""))[1]


def week_start(day: date | None = None) -> date:
    """The Monday of `day`'s week (local date by default)."""
    day = day or timezone.localdate()
    return day - timedelta(days=day.weekday())


def resets_on(day: date | None = None) -> date:
    """The next Monday — when the current week's race ends and leagues update."""
    return week_start(day) + timedelta(days=7)


def movement_counts(size: int, tier: int) -> tuple[int, int]:
    """How many of a tier of `size` students get promoted and relegated.

    Roughly `PROMOTE_FRACTION` each way, but at least one when the tier has
    anyone to move, never everyone, and never off the top or bottom tier. If the
    two zones would overlap in a tiny tier, relegation gives way so nobody is
    both promoted and relegated."""
    if size < 2:
        return 0, 0
    base = max(1, round(size * PROMOTE_FRACTION))
    promote = 0 if tier >= MAX_TIER else base
    demote = 0 if tier <= MIN_TIER else base
    if promote + demote > size:
        demote = max(0, size - promote)
    return promote, demote


def _weekly_xp(organization_id: int, since: date, until: date | None = None) -> dict[int, int]:
    """`{student_id: XP}` earned in [since, until) for one organization. `until`
    open-ended means "up to now"."""
    rows = XPTransaction.objects.filter(
        organization_id=organization_id, created_at__date__gte=since
    )
    if until is not None:
        rows = rows.filter(created_at__date__lt=until)
    rows = rows.values("student_id").annotate(total=Sum("amount"))
    return {row["student_id"]: row["total"] or 0 for row in rows}


def _org_students(organization_id: int):
    return StudentProfile.objects.filter(user__active_organization_id=organization_id)


def ensure_standings(organization_id: int) -> None:
    """Make sure every active student in the org has a standing (Bronza) and a
    weekly goal. New students join at the bottom tier."""
    existing_standings = set(
        LeagueStanding.objects.filter(organization_id=organization_id).values_list(
            "student_id", flat=True
        )
    )
    existing_goals = set(
        WeeklyGoal.objects.filter(organization_id=organization_id).values_list(
            "student_id", flat=True
        )
    )
    student_ids = list(_org_students(organization_id).values_list("id", flat=True))
    LeagueStanding.objects.bulk_create(
        [
            LeagueStanding(organization_id=organization_id, student_id=sid, tier=MIN_TIER)
            for sid in student_ids
            if sid not in existing_standings
        ]
    )
    WeeklyGoal.objects.bulk_create(
        [
            WeeklyGoal(
                organization_id=organization_id, student_id=sid, target_xp=DEFAULT_WEEKLY_GOAL
            )
            for sid in student_ids
            if sid not in existing_goals
        ]
    )


def get_or_create_standing(user) -> LeagueStanding:
    standing, _created = LeagueStanding.objects.get_or_create(
        organization_id=user.active_organization_id,
        student=user.student_profile,
        defaults={"tier": MIN_TIER},
    )
    return standing


def tier_summary(organization_id: int, my_tier: int | None = None) -> list[dict]:
    """One row per tier for the chips: number, name, icon, member count."""
    counts = dict(
        LeagueStanding.objects.filter(organization_id=organization_id)
        .values("tier")
        .annotate(n=Count("id"))
        .values_list("tier", "n")
    )
    return [
        {
            "tier": number,
            "name": name,
            "icon": icon,
            "count": counts.get(number, 0),
            "is_mine": number == my_tier,
        }
        for number, name, icon in LEAGUE_TIERS
    ]


def _avatar_url(student, request) -> str | None:
    avatar = student.user.avatar
    if not avatar:
        return None
    return request.build_absolute_uri(avatar.url) if request else avatar.url


def board(user, tier: int | None = None, request=None) -> dict:
    """The league board for `user`: the ranked members of a tier (their own by
    default), the promotion/relegation zones, and their own position."""
    organization_id = user.active_organization_id
    ensure_standings(organization_id)
    my_standing = get_or_create_standing(user)
    my_student_id = user.student_profile.id
    view_tier = tier if tier in _TIER_META else my_standing.tier

    standings = list(
        LeagueStanding.objects.filter(
            organization_id=organization_id, tier=view_tier
        ).select_related("student__user", "student__school_class")
    )
    xp_map = _weekly_xp(organization_id, week_start())
    standings.sort(
        key=lambda s: (-xp_map.get(s.student_id, 0), str(s.student).lower())
    )

    size = len(standings)
    promote, demote = movement_counts(size, view_tier)
    members = []
    my_rank = None
    my_weekly_xp = 0
    for index, standing in enumerate(standings):
        rank = index + 1
        student = standing.student
        is_me = standing.student_id == my_student_id
        xp = xp_map.get(standing.student_id, 0)
        if is_me:
            my_rank = rank
            my_weekly_xp = xp
        members.append(
            {
                "rank": rank,
                "name": str(student),
                "avatar_url": _avatar_url(student, request),
                "school_class_name": student.school_class.name if student.school_class else None,
                "weekly_xp": xp,
                "is_me": is_me,
                "zone": (
                    "up" if rank <= promote else "down" if rank > size - demote else "stay"
                ),
            }
        )

    return {
        "tier": view_tier,
        "tier_name": tier_name(view_tier),
        "tier_icon": tier_icon(view_tier),
        "my_tier": my_standing.tier,
        "week_start": week_start(),
        "resets_on": resets_on(),
        "promote_count": promote,
        "demote_count": demote,
        "my_rank": my_rank,
        "my_weekly_xp": my_weekly_xp,
        "members": members,
        "tiers": tier_summary(organization_id, my_standing.tier),
    }


def weekly_goal_status(user, request=None) -> dict:
    organization_id = user.active_organization_id
    goal, _created = WeeklyGoal.objects.get_or_create(
        organization_id=organization_id,
        student=user.student_profile,
        defaults={"target_xp": DEFAULT_WEEKLY_GOAL},
    )
    earned = _weekly_xp(organization_id, week_start()).get(user.student_profile.id, 0)
    return {
        "target_xp": goal.target_xp,
        "earned_xp": earned,
        "met": earned >= goal.target_xp,
        "goal_streak": goal.goal_streak,
        "best_goal_streak": goal.best_goal_streak,
        "week_start": week_start(),
        "resets_on": resets_on(),
    }


def set_weekly_goal(user, target_xp: int) -> WeeklyGoal:
    goal, _created = WeeklyGoal.objects.get_or_create(
        organization_id=user.active_organization_id,
        student=user.student_profile,
        defaults={"target_xp": target_xp},
    )
    goal.target_xp = target_xp
    goal.save(update_fields=["target_xp", "updated_at"])
    return goal


@transaction.atomic
def run_weekly_update(organization_id: int, today: date | None = None) -> dict:
    """Roll one organization's league over at the start of a new week: promote
    and relegate within each tier by the just-ended week's XP, and advance each
    student's weekly-goal streak. Idempotent per (org, ended week) via
    `LeagueCycle`. Returns a small summary for logging/tests."""
    today = today or timezone.localdate()
    this_monday = week_start(today)
    ended_week = this_monday - timedelta(days=7)

    _cycle, created = LeagueCycle.objects.get_or_create(
        organization_id=organization_id, week_start=ended_week
    )
    if not created:
        return {"skipped": True, "week": ended_week, "moved": 0, "goals_updated": 0}

    ensure_standings(organization_id)
    xp_map = _weekly_xp(organization_id, ended_week, this_monday)

    # --- Weekly goals -----------------------------------------------------
    goals_updated = 0
    for goal in WeeklyGoal.objects.filter(organization_id=organization_id):
        if goal.last_completed_week == ended_week:
            continue
        earned = xp_map.get(goal.student_id, 0)
        if earned >= goal.target_xp:
            goal.goal_streak += 1
            goal.best_goal_streak = max(goal.best_goal_streak, goal.goal_streak)
            goal.last_completed_week = ended_week
        else:
            goal.goal_streak = 0
        goal.save(
            update_fields=["goal_streak", "best_goal_streak", "last_completed_week", "updated_at"]
        )
        goals_updated += 1

    # --- Promotion / relegation ------------------------------------------
    standings_by_tier: dict[int, list[LeagueStanding]] = defaultdict(list)
    for standing in LeagueStanding.objects.filter(organization_id=organization_id):
        standings_by_tier[standing.tier].append(standing)

    moves: list[LeagueStanding] = []
    for tier, members in standings_by_tier.items():
        members.sort(key=lambda s: (-xp_map.get(s.student_id, 0), s.student_id))
        size = len(members)
        promote, demote = movement_counts(size, tier)
        for index, standing in enumerate(members):
            if index < promote:
                new_tier = min(tier + 1, MAX_TIER)
            elif index >= size - demote:
                new_tier = max(tier - 1, MIN_TIER)
            else:
                new_tier = tier
            if new_tier != tier:
                standing.tier = new_tier
                moves.append(standing)

    if moves:
        LeagueStanding.objects.bulk_update(moves, ["tier"])

    return {
        "skipped": False,
        "week": ended_week,
        "moved": len(moves),
        "goals_updated": goals_updated,
    }


def run_weekly_update_all(today: date | None = None) -> int:
    """Roll over every organization that has any league standings. Returns the
    number of organizations processed."""
    org_ids = (
        LeagueStanding.objects.values_list("organization_id", flat=True).distinct()
    )
    processed = 0
    for organization_id in list(org_ids):
        run_weekly_update(organization_id, today=today)
        processed += 1
    # New orgs that have students but no standings yet get bootstrapped so they
    # appear in the league from their first week.
    for organization in Organization.objects.all():
        if organization.id not in set(org_ids):
            ensure_standings(organization.id)
    return processed
