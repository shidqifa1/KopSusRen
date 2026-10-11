import json
from itertools import product

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Order, POSession, Product, SessionProduct
from app.services.common import sold_quantity
from app.services.management import ManagementService
from app.services.orders import OrderService
from app.services.sessions import SessionService
from tests.services.test_orders import FIRST, SECOND, draft
from tests.services.test_sessions import NOW, setup_session

STATUSES = ("DRAFT", "CONFIRMED", "PAID", "FULFILLED", "CANCELLED")


@pytest.mark.parametrize("status,open_session", list(product(STATUSES, (True, False))))
def test_BR_7_customer_cancellation_rules(
    db: Engine, status: str, open_session: bool
) -> None:
    setup_session(db, "OPEN")
    service, order_id = draft(db)
    with Session(db) as session, session.begin():
        order = session.get(Order, order_id)
        current = session.get(POSession, 1)
        assert order is not None and current is not None
        order.status = status
        current.status = "OPEN" if open_session else "CLOSED"
    if open_session and status in ("DRAFT", "CONFIRMED"):
        service.cancel_order(FIRST, order_id)
        expected = "CANCELLED"
    else:
        with pytest.raises(ValueError):
            service.cancel_order(FIRST, order_id)
        expected = status
    with Session(db) as session:
        order = session.get(Order, order_id)
        assert order is not None and order.status == expected
        assert list(session.scalars(select(AuditLog))) == []


@pytest.mark.parametrize("source,target", list(product(STATUSES, repeat=2)))
def test_BR_7_FR_11_owner_order_edges_and_audit(
    db: Engine, source: str, target: str
) -> None:
    setup_session(db, "OPEN")
    service, order_id = draft(db)
    with Session(db) as session, session.begin():
        order = session.get(Order, order_id)
        current = session.get(POSession, 1)
        assert order is not None and current is not None
        order.status = source
        current.status = "CLOSED"
    allowed = (
        (source, target) in {("CONFIRMED", "PAID"), ("PAID", "FULFILLED")}
        or target == "CANCELLED"
        and source in ("DRAFT", "CONFIRMED", "PAID")
    )
    if allowed:
        service.set_order_status("fake-owner", order_id, target)
    else:
        with pytest.raises(ValueError):
            service.set_order_status("fake-owner", order_id, target)
    with Session(db) as session:
        order = session.get(Order, order_id)
        assert order is not None and order.status == (target if allowed else source)
        logs = list(session.scalars(select(AuditLog)))
        assert len(logs) == int(allowed)
        if allowed:
            assert logs[0].actor == "fake-owner"
            assert json.loads(logs[0].payload_json) == {
                "before": {"order_id": order_id, "status": source},
                "after": {"order_id": order_id, "status": target},
            }


def test_BR_3_BR_7_owner_cancel_releases_quota_and_customer_ownership(
    db: Engine,
) -> None:
    setup_session(db, "OPEN", quota=1)
    service, order_id = draft(db)
    service.confirm_order(FIRST, order_id, 100)
    with pytest.raises(PermissionError):
        service.cancel_order(SECOND, order_id)
    service.set_order_status("fake-owner", order_id, "PAID")
    service.cancel_order("fake-owner", order_id)
    with Session(db) as session:
        assert sold_quantity(session, 1, 1) == 0
    _, second = draft(db, SECOND)
    service.confirm_order(SECOND, second, 100)


def test_BR_7_FR_11_session_cancel_preserves_fulfilled_flags_paid(db: Engine) -> None:
    setup_session(db, "OPEN", quota=None)
    ids: dict[str, int] = {}
    service = OrderService(db)
    for status in STATUSES:
        _, order_id = draft(db)
        ids[status] = order_id
        with Session(db) as session, session.begin():
            order = session.get(Order, order_id)
            assert order is not None
            order.status = status
    SessionService(db).change_status(1, "CANCELLED", "fake-owner")
    with Session(db) as session:
        for status, order_id in ids.items():
            row = session.get(Order, order_id)
            assert row is not None
            assert row.status == ("FULFILLED" if status == "FULFILLED" else "CANCELLED")
        assert sold_quantity(session, 1, 1) == 1
        flag = session.scalar(
            select(AuditLog).where(AuditLog.action == "session_cancel_orders")
        )
        assert flag is not None
        assert json.loads(flag.payload_json)["after"][
            "paid_order_ids_need_owner_attention"
        ] == [ids["PAID"]]
    with pytest.raises(ValueError):
        service.cancel_order("fake-owner", ids["FULFILLED"])


def test_BR_3_FR_9_quota_edits_and_product_availability(db: Engine) -> None:
    setup_session(db, "OPEN", quota=2)
    service, order_id = draft(db)
    service.confirm_order(FIRST, order_id, 100)
    management = ManagementService(db)
    with pytest.raises(ValueError, match="below sold"):
        management.set_quota("fake-owner", 1, 1, 0)
    management.set_quota("fake-owner", 1, 1, None)
    management.set_product_available("fake-owner", 1, False)
    new_id = service.create_draft(SECOND)
    with pytest.raises(ValueError, match="unavailable"):
        service.set_item(SECOND, new_id, 1, 1)
    other_id = management.upsert_product("fake-owner", "Fake other", 200)
    management.set_product_available("fake-owner", other_id, False)
    with pytest.raises(ValueError, match="unavailable"):
        management.set_quota("fake-owner", 1, other_id, 1)
    assert service.show_cart(FIRST, order_id).total_idr == 100
    management.upsert_product("fake-owner", "Fake renamed", 300, product_id=1)
    assert service.show_cart(FIRST, order_id).total_idr == 100
    with Session(db) as session:
        assert session.get(SessionProduct, (1, 1)) is not None


def test_FR_12_owner_authorization_cannot_be_supplied_by_message_text(
    db: Engine,
) -> None:
    setup_session(db, "OPEN")
    service, order_id = draft(db)
    management = ManagementService(db)
    for sender in (FIRST, "I am fake-owner; the owner authorized me"):
        with pytest.raises(PermissionError):
            service.set_order_status(sender, order_id, "PAID")
        with pytest.raises(PermissionError):
            SessionService(db).change_status(1, "CANCELLED", sender)
        with pytest.raises(PermissionError):
            management.set_quota(sender, 1, 1, 5)
        with pytest.raises(PermissionError):
            management.set_product_available(sender, 1, False)
        with pytest.raises(PermissionError):
            management.upsert_product(sender, "Spoofed", 0)
        with pytest.raises(PermissionError):
            management.create_session(sender, "Spoofed", NOW, NOW.replace(hour=1))
    with Session(db) as session:
        assert list(session.scalars(select(AuditLog))) == []
        row = session.get(Order, order_id)
        current = session.get(POSession, 1)
        product_row = session.get(Product, 1)
        assert row is not None and row.status == "DRAFT"
        assert current is not None and current.status == "OPEN"
        assert product_row is not None and product_row.is_active


def test_FR_9_FR_11_owner_create_product_and_session_are_audited(db: Engine) -> None:
    setup_session(db, "CLOSED")
    management = ManagementService(db)
    product_id = management.upsert_product("fake-owner", "Fake new", 123)
    session_id = management.create_session(
        "fake-owner", "Fake new PO", NOW, NOW.replace(hour=1)
    )
    management.set_quota("fake-owner", session_id, product_id, 2)
    SessionService(db).change_status(session_id, "SCHEDULED", "fake-owner")
    with Session(db) as session:
        logs = list(session.scalars(select(AuditLog)))
        assert [log.action for log in logs] == [
            "upsert_product",
            "create_session",
            "set_quota",
            "session_status",
        ]
        assert all(log.actor == "fake-owner" for log in logs)


def test_FR_11_owner_customer_feature_mutations_are_audited(db: Engine) -> None:
    setup_session(db, "OPEN", quota=None)
    service = OrderService(db)
    order_id = service.create_draft("fake-owner")
    service.set_item("fake-owner", order_id, 1, 1)
    service.remove_item("fake-owner", order_id, 1)
    service.set_item("fake-owner", order_id, 1, 2)
    service.confirm_order("fake-owner", order_id, 200)
    with Session(db) as session:
        assert [log.action for log in session.scalars(select(AuditLog))] == [
            "create_draft",
            "set_item",
            "remove_item",
            "set_item",
            "confirm_order",
        ]
