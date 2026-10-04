"""Builds the public `/p/<handle>/` profile card.

This is the only user data shown to anonymous visitors, so it is deliberately
narrow: a name, an avatar, and — for students — the gamified achievements that
make the profile worth sharing. It never exposes email, phone, PINFL, passport,
address, or any other identity field. Gamification imports `apps.users`, so the
gamification models are imported lazily here to avoid an import cycle.
"""


ROLE_LABEL = {
    "director": "Direktor",
    "teacher": "O'qituvchi",
    "student": "O'quvchi",
}


def _avatar_url(user, request) -> str | None:
    if not user.avatar:
        return None
    return request.build_absolute_uri(user.avatar.url) if request else user.avatar.url


def build_public_profile(user, request=None) -> dict:
    data = {
        "handle": user.handle,
        "full_name": user.get_full_name() or user.username,
        "avatar_url": _avatar_url(user, request),
        "role": user.role,
        "is_student": user.is_student,
        "is_teacher": user.is_teacher,
        "member_since": user.date_joined.year if user.date_joined else None,
    }

    if user.is_student:
        _add_student_card(user, data)
    elif user.is_teacher:
        teacher_profile = getattr(user, "teacher_profile", None)
        data["bio"] = teacher_profile.bio if teacher_profile else ""

    return data


def _add_student_card(user, data: dict) -> None:
    from apps.gamification.league import MIN_TIER, tier_icon, tier_name
    from apps.gamification.models import LeagueStanding, Streak, StudentAchievement

    profile = getattr(user, "student_profile", None)
    if profile is None:
        return
    org_id = user.active_organization_id

    data["school_class_name"] = profile.school_class.name if profile.school_class else None
    data["total_xp"] = profile.total_xp

    standings = LeagueStanding.objects.filter(student=profile)
    streaks = Streak.objects.filter(student=profile)
    achievements = StudentAchievement.objects.filter(student=profile).select_related("achievement")
    if org_id:
        standings = standings.filter(organization_id=org_id)
        streaks = streaks.filter(organization_id=org_id)
        achievements = achievements.filter(organization_id=org_id)

    standing = standings.first()
    tier = standing.tier if standing else MIN_TIER
    data["league"] = {"tier": tier, "name": tier_name(tier), "icon": tier_icon(tier)}

    streak = streaks.order_by("-current_streak").first()
    data["streak"] = {
        "current": streak.current_streak if streak else 0,
        "longest": streak.longest_streak if streak else 0,
    }

    data["achievements"] = [
        {
            "name": item.achievement.name,
            "icon": item.achievement.icon,
            "unlocked_at": item.unlocked_at,
        }
        for item in achievements
    ]


def build_full_profile(user, request=None) -> dict:
    """The complete, authenticated in-app view of one user — for a director.

    Builds on the public card (name, avatar, gamification) and layers on
    everything the public page deliberately hides: email, login, status, and
    every identity field (PINFL, passport, phone, address, …). Only ever reached
    through a director-gated, org-scoped endpoint.
    """
    data = build_public_profile(user, request=request)
    data.update(
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role_label": ROLE_LABEL.get(user.role, user.role),
            "is_active": user.is_active,
            "is_profile_public": user.is_profile_public,
            "date_joined": user.date_joined,
        }
    )

    if user.is_student:
        profile = getattr(user, "student_profile", None)
        if profile is not None:
            data.update(
                {
                    "middle_name": profile.middle_name,
                    "pinfl": profile.pinfl,
                    "passport_number": profile.passport_number,
                    "gender": profile.gender,
                    "gender_label": profile.get_gender_display() if profile.gender else "",
                    "birth_date": profile.birth_date,
                    "phone_number": profile.phone_number,
                    "parent_phone_number": profile.parent_phone_number,
                    "address": profile.address,
                    "region": profile.region,
                }
            )
    elif user.is_teacher:
        profile = getattr(user, "teacher_profile", None)
        if profile is not None:
            data["phone_number"] = profile.phone_number

    return data
