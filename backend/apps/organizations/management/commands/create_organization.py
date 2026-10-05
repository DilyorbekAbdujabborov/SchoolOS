"""Provision a real (paying/onboarding) organization and its first director.

Unlike ``seed_demo_org`` (fixed, shareable demo credentials), this creates one
tenant for an actual school/club and a single director account on a *generated*
temporary password that is printed exactly once. The director is forced to
change it on first login (``must_change_password=True``), mirroring the
bulk-import flow — the plaintext is never stored or shown again.

Idempotent on the organization and the director: rerunning with the same
``--slug`` keeps the org, and reusing the same ``--director-email`` keeps that
account (its password is only (re)generated with ``--reset-password``). The
``<slug>`` becomes the tenant's entrance at ``<slug>.<TENANT_BASE_DOMAIN>``; the
SSL sync job covers that host automatically within one interval.

Example::

    python manage.py create_organization \
        --name "Toshloq tumani 44-sonli umumiy o'rta ta'lim maktabi" \
        --slug toshloq-44 \
        --director-first Anorxan --director-last Nurmatova
"""

import secrets
import string

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Create a real organization (tenant) and its first director account."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True, help="Organization display name.")
        parser.add_argument(
            "--slug",
            required=True,
            help="Tenant slug; becomes <slug>.<TENANT_BASE_DOMAIN>. Lowercase, hyphens.",
        )
        parser.add_argument(
            "--type",
            default=Organization.Type.SCHOOL,
            choices=[c[0] for c in Organization.Type.choices],
            help="Organization type (default: SCHOOL).",
        )
        parser.add_argument("--director-first", required=True, help="Director first name.")
        parser.add_argument("--director-last", required=True, help="Director last name.")
        parser.add_argument(
            "--director-email",
            default=None,
            help="Director login email. Defaults to direktor@<slug>.<TENANT_BASE_DOMAIN>.",
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="If the director already exists, generate a new temporary password.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        raw_slug = options["slug"].strip().lower()
        slug = slugify(raw_slug)
        if slug != raw_slug:
            raise CommandError(
                f"Invalid slug '{options['slug']}'. Use lowercase letters, digits and hyphens "
                f"(suggested: '{slug}')."
            )

        from django.conf import settings

        base = (getattr(settings, "TENANT_BASE_DOMAIN", "") or "").strip().rstrip(".")
        email = options["director_email"] or (f"direktor@{slug}.{base}" if base else f"direktor@{slug}.local")

        org, org_created = Organization.objects.get_or_create(
            slug=slug,
            defaults={"name": options["name"], "type": options["type"]},
        )
        if not org_created and org.name != options["name"]:
            # Keep the row, but let an operator correct the display name.
            org.name = options["name"]
            org.save(update_fields=["name"])

        director, dir_created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "role": User.Role.DIRECTOR,
                "first_name": options["director_first"],
                "last_name": options["director_last"],
                "must_change_password": True,
                "is_active": True,
            },
        )

        temp_password = None
        if dir_created or options["reset_password"]:
            temp_password = _generate_temp_password()
            director.set_password(temp_password)
            director.must_change_password = True

        # Always pin the director to this org and keep identity fields current.
        director.first_name = options["director_first"]
        director.last_name = options["director_last"]
        director.role = User.Role.DIRECTOR
        director.is_active = True
        director.active_organization = org
        director.save()

        OrganizationMembership.objects.update_or_create(
            user=director,
            organization=org,
            defaults={
                "role": OrganizationMembership.Role.DIRECTOR,
                "status": OrganizationMembership.Status.ACTIVE,
            },
        )

        host = f"{slug}.{base}" if base else slug
        self.stdout.write(self.style.SUCCESS(
            f"Organization {'created' if org_created else 'exists'}: "
            f"'{org.name}' (slug={org.slug}, type={org.type})"
        ))
        self.stdout.write(f"  Entrance: https://{host}/")
        self.stdout.write(f"  Director: {director.first_name} {director.last_name} <{email}>")
        if temp_password is not None:
            self.stdout.write(self.style.WARNING(
                f"  Temporary password (shown ONCE): {temp_password}"
            ))
            self.stdout.write("  Director must change it on first login.")
        else:
            self.stdout.write(
                "  Director already existed; password unchanged "
                "(use --reset-password to regenerate)."
            )
