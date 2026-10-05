"""Attaches the subdomain's tenant to every request as `request.tenant`.

Runs before the view and before DRF authentication, so the auth layer and the
login view can pin the acting organization to the subdomain. Never raises: a bad
or unknown host just yields `request.tenant = None` (the main app).
"""

from django.conf import settings
from django.core.exceptions import DisallowedHost

from .tenancy import resolve_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        try:
            host = request.get_host()
        except DisallowedHost:
            host = request.META.get("HTTP_HOST", "")
        base_domain = getattr(settings, "TENANT_BASE_DOMAIN", "")
        if base_domain:
            request.tenant = resolve_tenant(host, base_domain)
        return self.get_response(request)
