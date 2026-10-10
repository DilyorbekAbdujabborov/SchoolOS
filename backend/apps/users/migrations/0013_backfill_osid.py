import secrets

from django.db import migrations

_OSID_BASE = 1_000_000_000
_OSID_SPAN = 9_000_000_000


def _backfill(apps, schema_editor):
    """Give every existing user a unique 10-digit OSID.

    A self-contained generator (not the one in services.py) so this migration
    stays valid even if that code later changes — migrations run against the
    historical model, not today's.
    """
    User = apps.get_model("users", "User")
    used = set(User.objects.exclude(osid__isnull=True).values_list("osid", flat=True))
    for user in User.objects.filter(osid__isnull=True).iterator():
        while True:
            candidate = str(_OSID_BASE + secrets.randbelow(_OSID_SPAN))
            if candidate not in used:
                used.add(candidate)
                break
        user.osid = candidate
        user.save(update_fields=["osid"])


def _noop(apps, schema_editor):
    # OSIDs are not removed on reverse — the column drop (0012 reverse) handles it.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0012_user_osid"),
    ]

    operations = [
        migrations.RunPython(_backfill, _noop),
    ]
