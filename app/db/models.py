from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps
from app.db.types import UTCDateTime


class Product(Timestamps, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("typeof(price_idr) = 'integer' AND price_idr >= 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    price_idr: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(default=True)


class POSession(Timestamps, Base):
    __tablename__ = "po_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','SCHEDULED','OPEN','CLOSED','CANCELLED')"),
        CheckConstraint("opens_at < closes_at"),
        Index(
            "uq_one_open_session",
            "status",
            unique=True,
            sqlite_where=text("status = 'OPEN'"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(default="DRAFT")
    opens_at: Mapped[datetime] = mapped_column(UTCDateTime())
    closes_at: Mapped[datetime] = mapped_column(UTCDateTime())
    auto_close_when_sold_out: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str | None] = mapped_column(Text)


class SessionProduct(Timestamps, Base):
    __tablename__ = "po_session_products"
    __table_args__ = (
        CheckConstraint("quota IS NULL OR (typeof(quota) = 'integer' AND quota >= 0)"),
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("po_sessions.id"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quota: Mapped[int | None] = mapped_column(Integer)


class Customer(Timestamps, Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone_e164: Mapped[str] = mapped_column(String, unique=True)
    display_name: Mapped[str | None] = mapped_column(String)


class Order(Timestamps, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT','CONFIRMED','PAID','FULFILLED','CANCELLED')"
        ),
        CheckConstraint("typeof(total_idr) = 'integer' AND total_idr >= 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("po_sessions.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(default="DRAFT")
    total_idr: Mapped[int] = mapped_column(default=0)
    note: Mapped[str | None] = mapped_column(Text)


class OrderItem(Timestamps, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("typeof(quantity) = 'integer' AND quantity > 0"),
        CheckConstraint(
            "unit_price_idr IS NULL OR "
            "(typeof(unit_price_idr) = 'integer' AND unit_price_idr >= 0)"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_idr: Mapped[int | None] = mapped_column(Integer)


class OwnerNumber(Timestamps, Base):
    __tablename__ = "owner_numbers"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone_e164: Mapped[str] = mapped_column(String, unique=True)
    label: Mapped[str | None] = mapped_column(String)


class Message(Timestamps, Base):
    __tablename__ = "messages"
    __table_args__ = (CheckConstraint("direction IN ('in','out')"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_message_id: Mapped[str] = mapped_column(String, unique=True)
    direction: Mapped[str] = mapped_column(String)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    text: Mapped[str] = mapped_column(Text)


class AuditLog(Timestamps, Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    payload_json: Mapped[str] = mapped_column(Text)
