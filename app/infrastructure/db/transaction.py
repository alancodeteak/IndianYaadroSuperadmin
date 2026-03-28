"""
Transaction boundaries for the service layer.

Repositories should call ``flush()`` (and ``refresh()``) only; services own
``commit()`` / ``rollback()`` so multi-step operations stay atomic when needed.

Session lifecycle: one ``Session`` per HTTP request (``get_db_session``) or per
job invocation — never store sessions on singleton services.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def session_commit_scope(session: Session) -> Generator[Session, None, None]:
    """
    Commit on successful exit; rollback on any exception.
    Use for a single logical write transaction initiated from a service.
    """
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
