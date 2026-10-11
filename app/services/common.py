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


def is_owner(session: Session, sender: str) -> bool:
    from app.db.models import OwnerNumber

    return (
        session.scalar(select(OwnerNumber.id).where(OwnerNumber.phone_e164 == sender))
        is not None
    )


def require_owner(session: Session, sender: str) -> None:
    if not is_owner(session, sender):
        raise PermissionError("Sender is not an owner")


def cancel_session_orders(session: Session, session_id: int, actor: str) -> None:
    from app.domain.orders import transition_order

    orders = list(
        session.scalars(
            select(Order).where(
                Order.session_id == session_id,
                Order.status.not_in(["FULFILLED", "CANCELLED"]),
            )
        )
    )
    paid_ids = [order.id for order in orders if order.status == "PAID"]
    for order in orders:
        before = {"order_id": order.id, "status": order.status}
        order.status = transition_order(
            order.status, "CANCELLED", owner=True, session_open=False
        )
        audit(
            session,
            actor,
            "session_cancel_order",
            before,
            {"order_id": order.id, "status": order.status},
        )
    audit(
        session,
        actor,
        "session_cancel_orders",
        {"session_id": session_id},
        {"session_id": session_id, "paid_order_ids_need_owner_attention": paid_ids},
    )
