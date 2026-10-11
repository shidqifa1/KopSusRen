from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from app.db.models import POSession
from app.db.types import jakarta_time


def test_BR_8_utc_round_trip(db: Engine) -> None:
    local = datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=7)))
    with Session(db) as session, session.begin():
        session.add(
            POSession(
                id=1, title="Fake", opens_at=local, closes_at=local + timedelta(hours=1)
            )
        )
    with Session(db) as session:
        row = session.get(POSession, 1)
        assert row is not None
        assert row.opens_at == local.astimezone(UTC)
        assert row.opens_at.tzinfo == UTC
        assert jakarta_time(row.opens_at).hour == 7
        assert row.created_at.tzinfo == UTC
        assert row.updated_at.tzinfo == UTC


def test_BR_8_naive_timestamp_is_rejected(db: Engine) -> None:
    with pytest.raises(StatementError), Session(db) as session, session.begin():
        session.add(
            POSession(
                title="Fake",
                opens_at=datetime(2026, 1, 1),
                closes_at=datetime(2026, 1, 2),
            )
        )
