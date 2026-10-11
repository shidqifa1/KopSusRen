from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import Customer, Message
from app.db.session import create_db_engine
from app.services.messages import MessageService
from tests.services.test_orders import FIRST, SECOND


def test_BR_9_inbound_duplicate_persists_across_restart(db: Engine) -> None:
    first = MessageService(db).record_inbound_message(
        "fake-message", FIRST, "Fake text"
    )
    assert first.duplicate is False
    url = str(db.url)
    db.dispose()
    fresh = create_db_engine(url)
    second = MessageService(fresh).record_inbound_message(
        "fake-message", SECOND, "Replacement"
    )
    assert second.duplicate is True and second.message_id == first.message_id
    with Session(fresh) as session:
        messages = list(session.scalars(select(Message)))
        assert len(messages) == 1 and messages[0].text == "Fake text"
        assert len(list(session.scalars(select(Customer)))) == 1
    fresh.dispose()


def test_BR_9_concurrent_duplicate_claim_exactly_once(db: Engine) -> None:
    barrier = Barrier(2)
    service = MessageService(db)

    def record(index: int) -> bool:
        barrier.wait(timeout=10)
        return service.record_inbound_message(
            "fake-concurrent", FIRST, "Fake"
        ).duplicate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(record, (1, 2)))
    assert sorted(results) == [False, True]
    with Session(db) as session:
        assert len(list(session.scalars(select(Message)))) == 1
        assert len(list(session.scalars(select(Customer)))) == 1


def test_BR_9_missing_provider_id_has_no_side_effect(db: Engine) -> None:
    with pytest.raises(ValueError):
        MessageService(db).record_inbound_message("", FIRST, "Fake")
    with Session(db) as session:
        assert list(session.scalars(select(Message))) == []
        assert list(session.scalars(select(Customer))) == []
