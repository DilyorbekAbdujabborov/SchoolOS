import logging

from celery import shared_task

from . import league

logger = logging.getLogger(__name__)


@shared_task
def run_league_promotion() -> int:
    """Roll every organization's weekly league over to the new week — promote and
    relegate within each tier by last week's XP and advance weekly-goal streaks.

    Celery Beat runs this every Monday just after midnight (see
    CELERY_BEAT_SCHEDULE). It is idempotent per (organization, week): the first
    run on a Monday does the work, any re-run that day is a no-op, so a worker
    restart cannot move students twice.
    """
    processed = league.run_weekly_update_all()
    logger.info("League weekly roll-up processed %s organization(s)", processed)
    return processed
