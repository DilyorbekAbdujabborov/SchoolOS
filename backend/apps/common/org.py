"""Helpers for resolving which organization (tenant) a row belongs to.

The multi-tenancy rollout made `organization` a NOT NULL FK on most models but
left it to callers to populate — so any `.create()` that forgot it raised an
IntegrityError at runtime. These helpers give model `save()` methods a single,
consistent way to derive the tenant from a related object, so the column can
never be left NULL regardless of the call site.
"""


def org_id_from_student(student) -> int | None:
    """A student's tenant: their class's organization, or their account's
    active one when they have no class yet.
    """
    if student is None:
        return None
    if getattr(student, "school_class_id", None):
        return student.school_class.organization_id
    user = getattr(student, "user", None)
    return getattr(user, "active_organization_id", None)


def org_id_from_user(user) -> int | None:
    """A user's active tenant."""
    return getattr(user, "active_organization_id", None) if user is not None else None
