import logging

from celery import shared_task
from django.db.models import Count

from apps.academics.models import Subject
from apps.schools.models import SchoolClass

from . import services
from .models import PooledQuestion

logger = logging.getLogger(__name__)


@shared_task
def refill_low_pools() -> int:
    """Tops up every existing subject+class pool running low on questions —
    Celery Beat re-runs this on a fixed interval (see CELERY_BEAT_SCHEDULE).

    Only touches combos that already have at least one pooled question; a
    brand new subject+class pool is bootstrapped by a director's manual
    "to'ldirish" action instead, so this task never fires a surprise Gemini
    call for a combo nobody has set up yet.
    """
    low_pools = list(
        PooledQuestion.objects.values("subject", "school_class")
        .annotate(count=Count("id"))
        .filter(count__lt=services.POOL_LOW_THRESHOLD)
    )

    # Batch-fetch every referenced Subject/SchoolClass once instead of two
    # `.get()` queries per low pool — with N low pools this was 1 + 2N
    # queries, now it's a constant 3 regardless of N.
    subjects = {
        s.id: s for s in Subject.objects.filter(id__in={row["subject"] for row in low_pools})
    }
    school_classes = {
        c.id: c for c in SchoolClass.objects.filter(id__in={row["school_class"] for row in low_pools})
    }

    refilled = 0
    for row in low_pools:
        subject = subjects[row["subject"]]
        school_class = school_classes[row["school_class"]]
        added = services.refill_pool(subject=subject, school_class=school_class)
        if added:
            refilled += 1
        else:
            logger.warning("Pool refill produced nothing for %s / %s", subject, school_class)

    return refilled
