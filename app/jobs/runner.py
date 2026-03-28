"""
Job execution adapter (scheduler-agnostic).

Call ``run_job(fn, db)`` from a cron entrypoint, Celery task, RQ worker, or
asyncio loop. This module does not pull in Celery/RQ — wire those in your
deployment layer and invoke the same ``app.jobs.*`` functions passed here.

Example (future Celery)::

    @celery_app.task
    def monthly_invoices():
        with SessionLocal() as db:
            return run_job(run_monthly_invoice_generation_job, db)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


def run_job(fn: Callable[[Session], T], db: Session) -> T:
    """Run a job function that accepts a DB session; caller owns session lifecycle."""
    return fn(db)
