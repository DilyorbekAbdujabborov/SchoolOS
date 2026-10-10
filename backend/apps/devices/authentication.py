"""Bearer-token authentication for the bridge-facing API.

A bridge authenticates with the opaque token it was issued (`Bridge.issue_token`).
Unlike the user-facing JWT auth, this resolves the *organization* from the token
alone — no user, no `X-Organization-Id` — so a bridge can only ever act inside its
own school. On success it sets `request.bridge` and `request.organization`, mirroring
how `OrganizationJWTAuthentication` attaches the acting organization.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions

from .models import Bridge

_PREFIX = "Bearer "


class BridgeTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("latin-1")
        if not header.startswith(_PREFIX):
            return None
        token = header[len(_PREFIX):].strip()
        if not token:
            return None

        # Only active bridges can authenticate. check_password is deliberately slow,
        # so this is O(active bridges) hashes per request — fine at current scale; a
        # token-prefix index is the optimization if bridge counts grow large.
        for bridge in Bridge.objects.filter(is_active=True).select_related("organization"):
            if bridge.check_token(token):
                request.bridge = bridge
                request.organization = bridge.organization
                bridge_org_id = bridge.organization_id
                request.organization_id = bridge_org_id
                return (bridge, None)

        raise exceptions.AuthenticationFailed(_("Bridge token yaroqsiz."))

    def authenticate_header(self, request):
        return "Bearer"
