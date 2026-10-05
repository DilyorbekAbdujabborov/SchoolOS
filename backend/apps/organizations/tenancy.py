"""Resolve which tenant (organization) a request's *subdomain* names.

The platform is multi-tenant by subdomain: `<org-slug>.tochna.uz` is that
organization's own entrance, while reserved hosts (`app.tochna.uz`, the bare
domain, the legacy `crm.sharqsoft.uz`) are the shared/main app and name no
tenant. `TenantMiddleware` runs this once per request and stores the result on
`request.tenant`; the auth layer then pins the acting organization to it, so a
visitor on `maktab1.tochna.uz` always acts in maktab1 (or is refused if they are
not a member) regardless of what their token claims.

Dormant until the wildcard DNS/SSL for `*.tochna.uz` is live — on every current
host the slug comes back None and nothing changes.
"""

import re

#: Subdomains that are the main app or infrastructure, never a tenant.
RESERVED_SUBDOMAINS = frozenset(
    {"", "app", "www", "api", "admin", "static", "media", "assets", "mail", "ftp"}
)

#: A valid DNS label (and therefore a valid tenant slug): 1–63 chars, lowercase
#: letters/digits/hyphen, no hyphen at either edge.
TENANT_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class InvalidTenantSlug(ValueError):
    """Raised by `validate_tenant_slug` with a human-readable Uzbek message."""


def validate_tenant_slug(value: str | None) -> str:
    """Normalise and validate an organization slug used as a subdomain.

    The slug becomes `<slug>.tochna.uz`, so it must be a legal DNS label and
    must not collide with a reserved/main-app subdomain. Returns the normalised
    (lowercased) slug or raises `InvalidTenantSlug`.
    """
    slug = (value or "").strip().lower()
    if not slug:
        raise InvalidTenantSlug("Slug bo'sh bo'lmasligi kerak.")
    if not TENANT_SLUG_RE.match(slug):
        raise InvalidTenantSlug(
            "Slug 1-63 ta belgi: faqat kichik harf, raqam va defis "
            "(boshida/oxirida defis bo'lmasin)."
        )
    if slug in RESERVED_SUBDOMAINS:
        raise InvalidTenantSlug("Bu slug band (tizim subdomeni) — boshqasini tanlang.")
    return slug


def tenant_slug_from_host(host: str | None, base_domain: str | None) -> str | None:
    """The single-label subdomain of `base_domain` in `host`, or None.

    `maktab1.tochna.uz` -> "maktab1"; `app.tochna.uz` -> None (reserved);
    `tochna.uz` -> None (no subdomain); `a.b.tochna.uz` -> None (not one label);
    any host not under `base_domain` -> None.
    """
    host = (host or "").split(":")[0].strip().lower().rstrip(".")
    base_domain = (base_domain or "").strip().lower().rstrip(".")
    if not host or not base_domain:
        return None

    suffix = f".{base_domain}"
    if not host.endswith(suffix):
        return None

    label = host[: -len(suffix)]
    if not label or "." in label:
        return None
    if label in RESERVED_SUBDOMAINS:
        return None
    return label


def resolve_tenant(host: str | None, base_domain: str | None):
    """The active `Organization` named by `host`'s subdomain, or None."""
    slug = tenant_slug_from_host(host, base_domain)
    if slug is None:
        return None
    from .models import Organization

    return Organization.objects.filter(slug=slug, is_active=True).first()
