from datetime import datetime

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import POSession, Product, SessionProduct
from app.domain.sessions import transition_session
from app.services.common import (
    audit,
    cancel_session_orders,
    require_owner,
    require_utc,
    sold_quantity,
    transaction,
)


class SessionService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def change_status(self, session_id: int, target: str, actor: str) -> None:
        with transaction(self.engine) as db:
            require_owner(db, actor)
            row = db.get(POSession, session_id)
            if row is None:
                raise ValueError("Unknown session")
            self._change(db, row, target, actor)

    def _change(self, db: Session, row: POSession, target: str, actor: str) -> None:
        destination = transition_session(row.status, target)
        if destination == "SCHEDULED":
            active = db.scalar(
                select(Product.id)
                .join(SessionProduct)
                .where(SessionProduct.session_id == row.id, Product.is_active.is_(True))
            )
            if active is None:
                raise ValueError("Scheduling requires an active product")
            overlap = db.scalar(
                select(POSession.id).where(
                    POSession.id != row.id,
                    POSession.status.in_(["SCHEDULED", "OPEN"]),
                    POSession.opens_at < row.closes_at,
                    POSession.closes_at > row.opens_at,
                )
            )
            if overlap is not None:
                raise ValueError("Overlapping session windows")
        if destination == "OPEN":
            if db.scalar(select(POSession.id).where(POSession.status == "OPEN")):
                raise ValueError("A session is already OPEN")
        before = {"session_id": row.id, "status": row.status}
        row.status = destination
        if destination == "CANCELLED":
            cancel_session_orders(db, row.id, actor)
        audit(
            db,
            actor,
            "session_status",
            before,
            {"session_id": row.id, "status": row.status},
        )
        db.flush()

    def run_tick(self, now: datetime) -> list[int]:
        now = require_utc(now)
        changed: list[int] = []
        with transaction(self.engine) as db:
            rows = list(
                db.scalars(
                    select(POSession)
                    .where(POSession.status.in_(["OPEN", "SCHEDULED"]))
                    .order_by(POSession.opens_at, POSession.id)
                )
            )
            # Close existing OPEN sessions before opening due scheduled sessions.
            for row in rows:
                if row.status == "OPEN" and (
                    now >= row.closes_at or self._sold_out(db, row)
                ):
                    self._change(db, row, "CLOSED", "scheduler")
                    changed.append(row.id)
            for row in rows:
                if row.status != "SCHEDULED" or now < row.opens_at:
                    continue
                if now >= row.closes_at:
                    self._change(db, row, "CANCELLED", "scheduler")
                    changed.append(row.id)
                elif (
                    db.scalar(select(POSession.id).where(POSession.status == "OPEN"))
                    is None
                ):
                    self._change(db, row, "OPEN", "scheduler")
                    changed.append(row.id)
                    if self._sold_out(db, row):
                        self._change(db, row, "CLOSED", "scheduler")
        return changed

    def _sold_out(self, db: Session, row: POSession) -> bool:
        products = list(
            db.scalars(
                select(SessionProduct).where(SessionProduct.session_id == row.id)
            )
        )
        return (
            row.auto_close_when_sold_out
            and bool(products)
            and all(
                product.quota is not None
                and sold_quantity(db, row.id, product.product_id) >= product.quota
                for product in products
            )
        )
