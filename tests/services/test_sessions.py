from datetime import UTC, datetime, timedelta
from itertools import product

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import AuditLog, POSession, Product, SessionProduct
from app.db.session import create_db_engine
from app.domain.sessions import EDGES, SessionStatus
from app.services.sessions import SessionService

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def setup_session(db: Engine, status: str = "DRAFT", quota: int | None = 1) -> None:
    with Session(db) as session, session.begin():
        session.add(Product(id=1, name="Fake", price_idr=100))
        session.add(
            POSession(
                id=1,
                title="Fake",
                status=status,
                opens_at=NOW,
                closes_at=NOW + timedelta(hours=1),
            )
        )
        session.flush()
        session.add(SessionProduct(session_id=1, product_id=1, quota=quota))


@pytest.mark.parametrize("source,target", list(product(SessionStatus, repeat=2)))
def test_BR_1_BR_4_every_session_status_pair(
    db: Engine, source: str, target: str
) -> None:
    setup_session(db, source)
    with Session(db) as session:
        original = session.get(POSession, 1)
        assert original is not None
        before = {
            column.key: getattr(original, column.key)
            for column in POSession.__table__.columns
        }
    service = SessionService(db)
    if SessionStatus(target) in EDGES[SessionStatus(source)]:
        service.change_status(1, target, "fake-owner")
        expected = target
    else:
        with pytest.raises(ValueError):
            service.change_status(1, target, "fake-owner")
        expected = source
    with Session(db) as session:
        row = session.get(POSession, 1)
        assert row is not None and row.status == expected
        if expected == source:
            assert {
                column.key: getattr(row, column.key)
                for column in POSession.__table__.columns
            } == before
            assert list(session.scalars(select(AuditLog))) == []


@pytest.mark.parametrize(
    "initial,expected", [("OPEN", "CLOSED"), ("SCHEDULED", "CANCELLED")]
)
def test_BR_4_restart_catch_up_is_idempotent(
    db: Engine, initial: str, expected: str
) -> None:
    setup_session(db, initial)
    url = str(db.url)
    db.dispose()
    fresh = create_db_engine(url)
    service = SessionService(fresh)
    assert service.run_tick(NOW + timedelta(hours=2)) == [1]
    assert service.run_tick(NOW + timedelta(hours=2)) == []
    with Session(fresh) as session:
        row = session.get(POSession, 1)
        assert row is not None and row.status == expected
        assert len(list(session.scalars(select(AuditLog)))) == 1
    fresh.dispose()


@pytest.mark.parametrize("quota,expected", [(0, "CLOSED"), (None, "OPEN"), (1, "OPEN")])
def test_BR_4_due_open_and_sold_out(
    db: Engine, quota: int | None, expected: str
) -> None:
    setup_session(db, "SCHEDULED", quota)
    assert SessionService(db).run_tick(NOW) == [1]
    with Session(db) as session:
        row = session.get(POSession, 1)
        assert row is not None and row.status == expected


def test_BR_4_schedule_requires_active_product_and_rejects_overlap(db: Engine) -> None:
    setup_session(db)
    service = SessionService(db)
    with Session(db) as session, session.begin():
        row = session.get(Product, 1)
        assert row is not None
        row.is_active = False
    with pytest.raises(ValueError, match="active"):
        service.change_status(1, "SCHEDULED", "fake-owner")
    with Session(db) as session, session.begin():
        row = session.get(Product, 1)
        assert row is not None
        row.is_active = True
        session.add(
            POSession(
                id=2,
                title="Overlap",
                status="SCHEDULED",
                opens_at=NOW,
                closes_at=NOW + timedelta(hours=2),
            )
        )
    with pytest.raises(ValueError, match="Overlapping"):
        service.change_status(1, "SCHEDULED", "fake-owner")


def test_BR_1_manual_open_requires_scheduled_and_no_other_open(db: Engine) -> None:
    setup_session(db, "SCHEDULED")
    with Session(db) as session, session.begin():
        session.add(
            POSession(
                id=2,
                title="Other",
                status="OPEN",
                opens_at=NOW,
                closes_at=NOW + timedelta(hours=2),
            )
        )
    with pytest.raises(ValueError, match="already OPEN"):
        SessionService(db).change_status(1, "OPEN", "fake-owner")
