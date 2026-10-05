"""Print every organization's tenant hostname, one per line.

Used by the server-side SSL sync job (``sync_tochna_ssl.sh``): it feeds the
output straight to ``certbot --expand`` and into the tenant nginx vhost's
``server_name`` so that every existing and future ``<slug>.<TENANT_BASE_DOMAIN>``
gets a valid, auto-renewing certificate without a DNS-01 token. Output is kept
deliberately plain (bare hosts, sorted, nothing else on stdout) so the shell can
consume it safely.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.organizations.models import Organization


class Command(BaseCommand):
    help = "Print one <slug>.<TENANT_BASE_DOMAIN> host per organization, sorted."

    def handle(self, *args, **options):
        base = (getattr(settings, "TENANT_BASE_DOMAIN", "") or "").strip().rstrip(".")
        if not base:
            return
        slugs = (
            Organization.objects.exclude(slug="")
            .values_list("slug", flat=True)
            .order_by("slug")
        )
        for slug in sorted(set(slugs)):
            self.stdout.write(f"{slug}.{base}")
