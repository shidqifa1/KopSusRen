from datetime import datetime

from sqlalchemy.engine import Engine

from app.db.models import POSession, Product, SessionProduct
from app.domain.orders import validate_money
from app.services.common import (
    audit,
    require_owner,
    require_utc,
    sold_quantity,
    transaction,
)


class ManagementService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create_session(
        self,
        sender: str,
        title: str,
        opens_at: datetime,
        closes_at: datetime,
        notes: str | None = None,
        auto_close_when_sold_out: bool = True,
    ) -> int:
        opens_at, closes_at = require_utc(opens_at), require_utc(closes_at)
        if opens_at >= closes_at:
            raise ValueError("Opening time must precede closing time")
        with transaction(self.engine) as db:
            require_owner(db, sender)
            row = POSession(
                title=title,
                opens_at=opens_at,
                closes_at=closes_at,
                notes=notes,
                auto_close_when_sold_out=auto_close_when_sold_out,
            )
            db.add(row)
            db.flush()
            audit(
                db,
                sender,
                "create_session",
                None,
                {
                    "session_id": row.id,
                    "title": title,
                    "status": row.status,
                    "opens_at": opens_at.isoformat(),
                    "closes_at": closes_at.isoformat(),
                    "notes": notes,
                    "auto_close_when_sold_out": auto_close_when_sold_out,
                },
            )
            return row.id

    def upsert_product(
        self,
        sender: str,
        name: str,
        price_idr: int,
        product_id: int | None = None,
        description: str | None = None,
    ) -> int:
        validate_money(price_idr)
        with transaction(self.engine) as db:
            require_owner(db, sender)
            row = db.get(Product, product_id) if product_id is not None else None
            if product_id is not None and row is None:
                raise ValueError("Unknown product")
            before = (
                None
                if row is None
                else {
                    "product_id": row.id,
                    "name": row.name,
                    "price_idr": row.price_idr,
                    "description": row.description,
                }
            )
            if row is None:
                row = Product(name=name, price_idr=price_idr, description=description)
                db.add(row)
            else:
                row.name, row.price_idr, row.description = name, price_idr, description
            db.flush()
            audit(
                db,
                sender,
                "upsert_product",
                before,
                {
                    "product_id": row.id,
                    "name": name,
                    "price_idr": price_idr,
                    "description": description,
                },
            )
            return row.id

    def set_product_available(
        self, sender: str, product_id: int, available: bool
    ) -> None:
        with transaction(self.engine) as db:
            require_owner(db, sender)
            row = db.get(Product, product_id)
            if row is None:
                raise ValueError("Unknown product")
            before = {"product_id": row.id, "is_active": row.is_active}
            row.is_active = available
            audit(
                db,
                sender,
                "product_available",
                before,
                {"product_id": row.id, "is_active": available},
            )

    def set_quota(
        self, sender: str, session_id: int, product_id: int, quota: int | None
    ) -> None:
        if quota is not None and (type(quota) is not int or quota < 0):
            raise ValueError("Quota must be NULL or a nonnegative integer")
        with transaction(self.engine) as db:
            require_owner(db, sender)
            if db.get(POSession, session_id) is None:
                raise ValueError("Unknown session")
            attached = db.get(SessionProduct, (session_id, product_id))
            product = db.get(Product, product_id)
            if product is None or (attached is None and not product.is_active):
                raise ValueError("Cannot attach unavailable product")
            if quota is not None and quota < sold_quantity(db, session_id, product_id):
                raise ValueError("Quota cannot fall below sold quantity")
            before = None if attached is None else {"quota": attached.quota}
            if attached is None:
                db.add(
                    SessionProduct(
                        session_id=session_id, product_id=product_id, quota=quota
                    )
                )
            else:
                attached.quota = quota
            audit(
                db,
                sender,
                "set_quota",
                before,
                {"session_id": session_id, "product_id": product_id, "quota": quota},
            )
