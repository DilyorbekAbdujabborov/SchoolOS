from rest_framework.permissions import BasePermission


class IsBridge(BasePermission):
    """Allow only requests authenticated as a `Bridge` (see
    `BridgeTokenAuthentication`)."""

    def has_permission(self, request, view) -> bool:
        return getattr(request, "bridge", None) is not None
