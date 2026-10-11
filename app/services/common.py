import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Order, OrderItem


@contextmanager
def transaction(engine: Engine) -> Iterator[Session]:
    with engine.connect().execution_options(sqlite_immediate=True) as connection:
        with connection.begin(), Session(bind=connection) as session:
            yield session
            session.flush()


def require_utc(now: datetime) -> datetime:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Time must be aware")
    return now.astimezone(UTC)


def sold_quantity(session: Session, session_id: int, product_id: int) -> int:
    return int(
        session.scalar(
            select(func.coalesce(func.sum(OrderItem.quantity), 0))
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.session_id == session_id,
                OrderItem.product_id == product_id,
                Order.status.in_(["CONFIRMED", "PAID", "FULFILLED"]),
            )
        )
        or 0
    )


def audit(
    session: Session, actor: str, action: str, before: object, after: object
) -> None:
    session.add(
        AuditLog(
            actor=actor,
            action=action,
            payload_json=json.dumps({"before": before, "after": after}),
        )
    )
