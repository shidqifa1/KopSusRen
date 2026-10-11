from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Order, OwnerNumber, POSession, Product
from app.db.session import create_db_engine
from app.db.types import jakarta_time
from app.services.common import sold_quantity
from app.services.management import ManagementService
from app.services.messages import MessageService
from app.services.orders import OrderService
from app.services.sessions import SessionService
from tests.services.test_orders import FIRST, SECOND
from tests.services.test_sessions import NOW


def test_BR_1_BR_2_BR_3_BR_4_BR_5_BR_6_BR_7_BR_8_BR_9_BR_10_combined_acceptance(
    db: Engine,
) -> None:
    with Session(db) as session, session.begin():
        session.add(OwnerNumber(phone_e164="fake-owner"))
    management = ManagementService(db)
    sessions = SessionService(db)
    orders = OrderService(db)
    messages = MessageService(db)
    product_id = management.upsert_product("fake-owner", "Fake coffee", 10000)
    po_id = management.create_session(
        "fake-owner",
        "Fake PO",
        NOW,
        NOW + timedelta(hours=1),
        notes="Fake pickup notes",
    )
    management.set_quota("fake-owner", po_id, product_id, 2)
    with pytest.raises(ValueError, match="OPEN"):
        orders.create_draft(FIRST)
    sessions.change_status(po_id, "SCHEDULED", "fake-owner")
    assert sessions.run_tick(NOW) == [po_id]
    order_id = orders.create_draft(FIRST)
    with pytest.raises(ValueError):
        orders.set_item(FIRST, order_id, product_id, 21)
    orders.set_item(FIRST, order_id, product_id, 2)
    summary = orders.show_cart(FIRST, order_id)
    assert summary.total_idr == 20000 and type(summary.total_idr) is int
    assert summary.pickup_info == "Fake pickup notes"
    assert summary.items[0].line_total_idr == 20000
    confirmations = 0
    for _ in range(2):
        result = messages.record_inbound_message("fake-confirm", FIRST, "yes")
        if not result.duplicate:
            orders.confirm_order(FIRST, order_id, summary.total_idr)
            confirmations += 1
    assert confirmations == 1
    management.upsert_product("fake-owner", "Fake coffee", 12000, product_id=product_id)
    assert orders.show_cart(FIRST, order_id).total_idr == 20000
    other = orders.create_draft(SECOND)
    orders.set_item(SECOND, other, product_id, 1)
    with pytest.raises(ValueError, match="quota"):
        orders.confirm_order(SECOND, other, 12000)
    assert sessions.run_tick(NOW) == [po_id]  # Finite quotas exhausted.
    with pytest.raises(ValueError):
        orders.cancel_order(FIRST, order_id)
    orders.cancel_order("fake-owner", order_id)
    with Session(db) as session:
        assert sold_quantity(session, po_id, product_id) == 0
        current = session.get(POSession, po_id)
        assert current is not None and current.status == "CLOSED"
        assert jakarta_time(current.opens_at).hour == 7
        row = session.get(Order, other)
        assert row is not None and row.status == "DRAFT"
        assert list(session.scalars(select(AuditLog)))


def test_BR_1_BR_4_restart_closes_before_opening_next_session(db: Engine) -> None:
    with Session(db) as session, session.begin():
        session.add(OwnerNumber(phone_e164="fake-owner"))
    management = ManagementService(db)
    product_id = management.upsert_product("fake-owner", "Fake", 100)
    first = management.create_session(
        "fake-owner", "First", NOW, NOW + timedelta(hours=1)
    )
    second = management.create_session(
        "fake-owner", "Next", NOW + timedelta(hours=1), NOW + timedelta(hours=2)
    )
    management.set_quota("fake-owner", first, product_id, None)
    management.set_quota("fake-owner", second, product_id, None)
    service = SessionService(db)
    service.change_status(first, "SCHEDULED", "fake-owner")
    service.change_status(second, "SCHEDULED", "fake-owner")
    service.run_tick(NOW)
    url = str(db.url)
    db.dispose()
    fresh = create_db_engine(url)
    restarted = SessionService(fresh)
    assert restarted.run_tick(NOW + timedelta(hours=1)) == [first, second]
    assert restarted.run_tick(NOW + timedelta(hours=1)) == []
    with Session(fresh) as session:
        first_row = session.get(POSession, first)
        second_row = session.get(POSession, second)
        assert first_row is not None and first_row.status == "CLOSED"
        assert second_row is not None and second_row.status == "OPEN"
        assert len(list(session.scalars(select(Product)))) == 1
    fresh.dispose()
