"""Resolves the organization a request is acting in.

DRF gives views a `request`, and everything downstream needs `request.organization`
and `request.organization_membership`. Rather than repeating the lookup in every
view, an authentication class fills it once, in `authenticate()` — which DRF calls
for every request that carries credentials.

The `org_id` claim is the source of truth. It is set at login and re-set by
`/api/switch-organization/`, so switching organizations takes effect on the very
next request instead of waiting for a token to expire. A claim naming an
organization the user isn't an active member of is rejected outright (403) rather
than silently downgraded — a tampered or stale token must not fall back to "any
membership", because with two organizations on one account that would mean
granting the wrong permissions.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.organizations import services
from apps.organizations.capabilities import capability_for, get_denied, is_allowed

#: The JWT claim naming the active organization.
ORG_CLAIM = "org_id"


def _apply_membership(request, user, membership) -> None:
    """Make `membership` the acting organization for this request *and* for the
    user object the views see.

    Two layers read "the current organization": `request.organization` (set by
    this auth class) and `user.active_membership` / `user.active_organization`
    (read directly by querysets like StudentViewSet and by all gamification). If
    only the request side were set, a token claim, an `X-Organization-Id` header
    or a tenant subdomain would re-scope some endpoints but not others. Binding
    both — in memory, never persisted here — keeps the whole request consistently
    inside one organization.
    """
    request.organization_membership = membership
    request.organization = membership.organization
    user.active_organization = membership.organization
    user._active_membership_cache = membership


class OrganizationJWTAuthentication(JWTAuthentication):
    """`JWTAuthentication` plus an active-organization membership on the request."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, token = result
        claim = token.get(ORG_CLAIM) if hasattr(token, "get") else None
        if claim is not None:
            try:
                claim = int(claim)
            except (TypeError, ValueError):
                raise exceptions.AuthenticationFailed(
                    _("Tokendagi tashkilot ma'lumoti noto'g'ri."), code="invalid_org"
                )

        request.user = user
        request.organization = None
        _apply_membership(request, user, services.resolve_membership(user, claim))
        return result


class OrganizationHeaderAuthentication(OrganizationJWTAuthentication):
    """Same as above, but an `X-Organization-Id` header wins over the token claim.

    Lets a client with several organizations act in one without holding several
    tokens. The header is only ever accepted when it names an organization the
    user is genuinely an active member of, so it cannot widen access.
    """

    HEADER = "HTTP_X_ORGANIZATION_ID"

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user = request.user

        header = request.META.get(self.HEADER)
        if header:
            try:
                organization_id = int(header)
            except (TypeError, ValueError):
                raise exceptions.AuthenticationFailed(
                    _("X-Organization-Id sarlavhasi noto'g'ri."), code="invalid_org"
                )
            _apply_membership(request, user, services.resolve_membership(user, organization_id))

        # A tenant subdomain is authoritative: on `<slug>.tochna.uz` the request
        # acts in that organization whatever the token claims, and a non-member
        # is refused (403) rather than silently acting in some other org. Wins
        # over both the claim and the X-Organization-Id header.
        tenant = getattr(request, "tenant", None)
        if tenant is not None:
            _apply_membership(request, user, services.resolve_membership(user, tenant.id))

        enforce_capabilities(request)
        return result


class CapabilityDenied(exceptions.APIException):
    # Not AppError: apps.common.exceptions imports rest_framework.views, which
    # loads this module via DEFAULT_AUTHENTICATION_CLASSES — a circular import.
    # The envelope reads `default_code` either way.
    status_code = 403
    default_detail = _("Bu bo'lim tashkilotingiz uchun yoqilmagan.")
    default_code = "capability_denied"

    def __init__(self, capability: str):
        # The key travels in the envelope's `errors.capability`, so the frontend
        # can tell which capability was refused.
        super().__init__(detail={"detail": self.default_detail, "capability": [capability]})
        self.capability = capability


def enforce_capabilities(request) -> None:
    """Refuse the request when the acting organization's client-config denies the
    capability its path and method need. Runs where the organization is final
    (end of `OrganizationHeaderAuthentication.authenticate`), so it never has to
    resolve the organization a second way."""
    organization = getattr(request, "organization", None)
    if organization is None:
        return
    key = capability_for(request.path, request.method)
    if key is None:
        return
    if not is_allowed(get_denied(organization), key):
        raise CapabilityDenied(key)


def organization_for_request(request):
    """`request.organization`, or None when the request was never authenticated
    with organization context (anonymous, or a non-JWT session)."""
    return getattr(request, "organization", None)


def organization_required(request):
    """`request.organization`, raising 403 if absent."""
    organization = organization_for_request(request)
    if organization is None:
        raise exceptions.PermissionDenied(_("Tashkilot konteksti talab qilinadi."))
    return organization


__all__ = [
    "ORG_CLAIM",
    "CapabilityDenied",
    "enforce_capabilities",
    "OrganizationHeaderAuthentication",
    "OrganizationJWTAuthentication",
    "organization_for_request",
    "organization_required",
]
