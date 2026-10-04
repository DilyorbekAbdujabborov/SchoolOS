"""Roll every organization's weekly league over to the new week.

This is the same work as the `apps.gamification.tasks.run_league_promotion`
Celery task, exposed as a management command so it can be driven by a plain
system cron where Celery Beat is not running. Intended to run every Monday just
after midnight. Idempotent per (organization, week), so a second run on the same
Monday is a harmless no-op.
"""

from django.core.management.base import BaseCommand

from apps.gamification import league


class Command(BaseCommand):
    help = "Promote/relegate students between league tiers for the week that just ended."

    def handle(self, *args, **options):
        processed = league.run_weekly_update_all()
        self.stdout.write(
            self.style.SUCCESS(f"League roll-up complete — {processed} organization(s) processed.")
        )
