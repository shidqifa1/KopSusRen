import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import Customer, Order, OrderItem, POSession, Product, SessionProduct
from app.domain.orders import PriceMismatch
from app.services.common import sold_quantity, transaction
from app.services.orders import OrderService
from tests.services.test_sessions import setup_session

FIRST = "+00000000001"
SECOND = "+00000000002"


def draft(
    db: Engine, sender: str = FIRST, quantity: int = 1
) -> tuple[OrderService, int]:
    service = OrderService(db)
    order_id = service.create_draft(sender)
    service.set_item(sender, order_id, 1, quantity)
    return service, order_id


def test_BR_3_begin_immediate_reserves_write_lock_before_any_write(db: Engine) -> None:
    observed: list[str] = []

    def observe(
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        observed.append(statement)

    event.listen(db, "before_cursor_execute", observe)
    with transaction(db):
        contender = sqlite3.connect(db.url.database or "", timeout=0)
        try:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                contender.execute("BEGIN IMMEDIATE")
        finally:
            contender.close()
    assert "BEGIN IMMEDIATE" in observed


def test_BR_3_concurrent_last_unit_exactly_one_success(db: Engine) -> None:
    setup_session(db, "OPEN", quota=1)
    service, first = draft(db)
    _, second = draft(db, SECOND)
    barrier = Barrier(2)

    def confirm(sender: str, order_id: int) -> bool:
        barrier.wait(timeout=10)
        try:
            service.confirm_order(sender, order_id, 100)
            return True
        except ValueError as exc:
            assert str(exc) == "Insufficient quota"
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda args: confirm(*args), [(FIRST, first), (SECOND, second)])
        )
    assert results.count(True) == 1
    with Session(db) as session:
        assert sold_quantity(session, 1, 1) == 1
        loser = second if results[0] else first
        row = session.get(Order, loser)
        assert row is not None and row.status == "DRAFT" and row.total_idr == 0
        item = session.scalar(select(OrderItem).where(OrderItem.order_id == loser))
        assert item is not None and item.unit_price_idr is None


def test_BR_3_multi_item_failure_rolls_back_all_snapshots(db: Engine) -> None:
    setup_session(db, "OPEN", quota=2)
    with Session(db) as session, session.begin():
        session.add(Product(id=2, name="Fake second", price_idr=200))
        session.flush()
        session.add(SessionProduct(session_id=1, product_id=2, quota=0))
    service, order_id = draft(db)
    service.set_item(FIRST, order_id, 2, 1)
    with pytest.raises(ValueError, match="quota"):
        service.confirm_order(FIRST, order_id, 300)
    with Session(db) as session:
        order = session.get(Order, order_id)
        assert order is not None and order.status == "DRAFT" and order.total_idr == 0
        assert all(
            item.unit_price_idr is None for item in session.scalars(select(OrderItem))
        )
        assert sold_quantity(session, 1, 1) == 0


def test_BR_5_FR_2_price_mismatch_refresh_and_repeat_confirmation(db: Engine) -> None:
    setup_session(db, "OPEN", quota=1)
    service, order_id = draft(db)
    assert service.show_cart(FIRST, order_id).total_idr == 100
    with Session(db) as session, session.begin():
        product = session.get(Product, 1)
        assert product is not None
        product.price_idr = 200
    with pytest.raises(PriceMismatch) as failure:
        service.confirm_order(FIRST, order_id, 100)
    assert failure.value.summary.total_idr == 200
    result = service.confirm_order(FIRST, order_id, 200)
    assert result.status == "CONFIRMED"
    with Session(db) as session, session.begin():
        product = session.get(Product, 1)
        assert product is not None
        product.price_idr = 300
    assert service.confirm_order(FIRST, order_id, 200) == result
    assert service.show_cart(FIRST, order_id) == result
    with Session(db) as session:
        assert sold_quantity(session, 1, 1) == 1


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, 21])
def test_BR_10_quantity_limits(db: Engine, quantity: int) -> None:
    setup_session(db, "OPEN")
    service = OrderService(db)
    order_id = service.create_draft(FIRST)
    with pytest.raises(ValueError):
        service.set_item(FIRST, order_id, 1, quantity)
    assert service.show_cart(FIRST, order_id).items == ()


def test_BR_10_configurable_limit_and_persistent_drafts(
    db: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_session(db, "OPEN", quota=None)
    monkeypatch.setenv("MAX_QTY_PER_ITEM", "2")
    service, order_id = draft(db, quantity=2)
    fresh = OrderService(db)
    assert fresh.show_cart(FIRST, order_id).items[0].quantity == 2
    with pytest.raises(ValueError):
        fresh.set_item(FIRST, order_id, 1, 3)
    fresh.remove_item(FIRST, order_id, 1)
    with pytest.raises(ValueError, match="empty"):
        service.confirm_order(FIRST, order_id, 0)


@pytest.mark.parametrize(
    "status", ["DRAFT", "CONFIRMED", "PAID", "FULFILLED", "CANCELLED"]
)
def test_BR_3_quota_counts_only_sold_statuses(db: Engine, status: str) -> None:
    setup_session(db, "OPEN", quota=1)
    service, first = draft(db)
    with Session(db) as session, session.begin():
        order = session.get(Order, first)
        assert order is not None
        order.status = status
    _, second = draft(db, SECOND)
    if status in ("CONFIRMED", "PAID", "FULFILLED"):
        with pytest.raises(ValueError, match="quota"):
            service.confirm_order(SECOND, second, 100)
    else:
        service.confirm_order(SECOND, second, 100)


def test_BR_2_BR_7_draft_ownership_session_and_availability(db: Engine) -> None:
    setup_session(db, "OPEN")
    service, order_id = draft(db)
    with pytest.raises(PermissionError):
        service.set_item(SECOND, order_id, 1, 1)
    with pytest.raises(ValueError, match="unavailable"):
        service.set_item(FIRST, order_id, 999, 1)
    with Session(db) as session, session.begin():
        product = session.get(Product, 1)
        assert product is not None
        product.is_active = False
    with pytest.raises(ValueError, match="unavailable"):
        service.confirm_order(FIRST, order_id, 100)
    with Session(db) as session, session.begin():
        current = session.get(POSession, 1)
        assert current is not None
        current.status = "CLOSED"
    with pytest.raises(ValueError, match="OPEN"):
        service.set_item(FIRST, order_id, 1, 1)
    with pytest.raises(ValueError, match="OPEN"):
        service.create_draft(SECOND)
    with Session(db) as session:
        assert len(list(session.scalars(select(Customer)))) == 1
