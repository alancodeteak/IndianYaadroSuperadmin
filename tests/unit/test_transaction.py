"""session_commit_scope commits on success and rolls back on failure."""

from unittest.mock import MagicMock

import pytest

from app.infrastructure.db.transaction import session_commit_scope


def test_session_commit_scope_commits_on_success() -> None:
    session = MagicMock()
    with session_commit_scope(session):
        pass
    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_session_commit_scope_rollbacks_on_error() -> None:
    session = MagicMock()

    def boom() -> None:
        with session_commit_scope(session):
            raise ValueError("x")

    with pytest.raises(ValueError):
        boom()
    session.rollback.assert_called_once()
    session.commit.assert_not_called()
