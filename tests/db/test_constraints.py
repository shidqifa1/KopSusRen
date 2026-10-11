from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    Customer,
    Message,
    Order,
    OrderItem,
    POSession,
    Product,
    SessionProduct,
)


def seed(db: Engine) -> None:
    now = datetime.now(UTC)
    with Session(db) as session, session.begin():
        session.add_all(
            [
                Product(id=1, name="Fake coffee", price_idr=100),
                Customer(id=1, phone_e164="+00000000001"),
                POSession(
                    id=1,
                    title="Fake PO",
                    opens_at=now,
                    closes_at=now + timedelta(hours=1),
                    status="OPEN",
                ),
                POSession(
                    id=2,
                    title="Fake next",
                    opens_at=now,
                    closes_at=now + timedelta(hours=1),
                ),
            ]
        )
        session.flush()
        session.add(Order(id=1, session_id=1, customer_id=1))
        session.flush()
        session.add(OrderItem(id=1, order_id=1, product_id=1, quantity=1))
        session.add(SessionProduct(session_id=1, product_id=1, quota=None))


@pytest.mark.parametrize("operation", ["insert", "update"])
def test_BR_1_migration_rejects_second_open_session(db: Engine, operation: str) -> None:
    seed(db)
    with pytest.raises(IntegrityError), db.begin() as connection:
        if operation == "update":
            connection.exec_driver_sql(
                "UPDATE po_sessions SET status='OPEN' WHERE id=2"
            )
        else:
            connection.exec_driver_sql(
                "INSERT INTO po_sessions SELECT 3,title,'OPEN',opens_at,closes_at,"
                "auto_close_when_sold_out,notes,created_at,updated_at "
                "FROM po_sessions WHERE id=1"
            )


@pytest.mark.parametrize("status", ["DRAFT", "SCHEDULED", "CLOSED", "CANCELLED"])
def test_BR_1_multiple_non_open_sessions_are_allowed(db: Engine, status: str) -> None:
    seed(db)
    with db.begin() as connection:
        connection.execute(
            text("UPDATE po_sessions SET status=:status"), {"status": status}
        )


@pytest.mark.parametrize("value", [None, 0, 1, -1, 0.5])
def test_BR_3_quota_accepts_null_and_zero_but_rejects_negative_or_fractional(
    db: Engine, value: int | float | None
) -> None:
    seed(db)
    if value is not None and (value < 0 or isinstance(value, float)):
        with pytest.raises(IntegrityError), db.begin() as connection:
            connection.execute(
                text("UPDATE po_session_products SET quota=:value"), {"value": value}
            )
    else:
        with db.begin() as connection:
            connection.execute(
                text("UPDATE po_session_products SET quota=:value"), {"value": value}
            )


@pytest.mark.parametrize(
    "table,column",
    [
        ("products", "price_idr"),
        ("orders", "total_idr"),
        ("order_items", "unit_price_idr"),
    ],
)
@pytest.mark.parametrize("value", [-1, 1.5])
def test_BR_6_money_rejects_fractional_values(
    db: Engine, table: str, column: str, value: int | float
) -> None:
    seed(db)
    with pytest.raises(IntegrityError), db.begin() as connection:
        connection.execute(
            text(f"UPDATE {table} SET {column}=:value"), {"value": value}
        )


@pytest.mark.parametrize("value", [0, -1, 1.5])
def test_BR_10_quantity_rejects_zero_negative_and_fractional(
    db: Engine, value: int | float
) -> None:
    seed(db)
    with pytest.raises(IntegrityError), db.begin() as connection:
        connection.execute(
            text("UPDATE order_items SET quantity=:value"), {"value": value}
        )


def test_BR_9_provider_message_id_is_unique(db: Engine) -> None:
    seed(db)
    with Session(db) as session, session.begin():
        session.add(
            Message(
                provider_message_id="fake-1", customer_id=1, direction="in", text="test"
            )
        )
    with pytest.raises(IntegrityError), Session(db) as session, session.begin():
        session.add(
            Message(
                provider_message_id="fake-1", customer_id=1, direction="in", text="test"
            )
        )


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE po_sessions SET status='INVALID'",
        "UPDATE orders SET status='INVALID'",
        "UPDATE po_sessions SET opens_at=closes_at",
        "UPDATE orders SET customer_id=999",
        "INSERT INTO po_session_products SELECT * FROM po_session_products",
    ],
)
def test_BR_1_schema_constraints(db: Engine, statement: str) -> None:
    seed(db)
    with pytest.raises(IntegrityError), db.begin() as connection:
        connection.exec_driver_sql(statement)


@pytest.mark.parametrize("model", [Product, POSession, Customer, Order])
def test_BR_5_order_history_prevents_parent_delete(
    db: Engine, model: type[Product] | type[POSession] | type[Customer] | type[Order]
) -> None:
    seed(db)
    with pytest.raises(IntegrityError), Session(db) as session, session.begin():
        session.execute(delete(model).where(model.id == 1))


def test_BR_9_direction_and_phone_constraints(db: Engine) -> None:
    seed(db)
    with pytest.raises(IntegrityError), Session(db) as session, session.begin():
        session.add(Customer(phone_e164="+00000000001"))
    with pytest.raises(IntegrityError), Session(db) as session, session.begin():
        session.add(
            Message(
                provider_message_id="fake-bad",
                direction="bad",
                customer_id=1,
                text="test",
            )
        )
