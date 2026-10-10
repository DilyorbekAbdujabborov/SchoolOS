from rest_framework.throttling import SimpleRateThrottle


class BridgeRateThrottle(SimpleRateThrottle):
    """Per-bridge rate limit. Keyed on the bridge's own pk under a `bridge_`
    prefix, so a Bridge and a User that happen to share a pk never share a
    budget (the default UserRateThrottle keys on bare `request.user.pk`)."""

    scope = "bridge"

    def get_cache_key(self, request, view):
        bridge = getattr(request, "bridge", None) or request.user
        return self.cache_format % {"scope": self.scope, "ident": f"bridge_{bridge.pk}"}
