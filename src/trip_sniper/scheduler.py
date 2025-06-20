from __future__ import annotations

import os
from celery import Celery
from celery.schedules import crontab

from . import pipeline

# Celery application configured with Redis broker
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("trip_sniper", broker=BROKER_URL)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs) -> None:
    """Register periodic tasks."""
    sender.add_periodic_task(
        crontab(minute=0, hour="*"),
        run_pipeline_task.s(),
        name="run pipeline hourly",
    )


@app.task(bind=True, max_retries=3, default_retry_delay=300, acks_late=True)
def run_pipeline_task(self) -> None:
    """Run the data pipeline. Idempotent due to upserts."""
    try:
        pipeline.run()
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)
