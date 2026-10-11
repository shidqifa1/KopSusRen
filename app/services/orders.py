import os

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.models import Customer, Order, OrderItem, POSession, Product, SessionProduct
from app.domain.orders import (
    OrderSummary,
    PriceMismatch,
    SummaryItem,
    transition_order,
    validate_money,
    validate_quantity,
)
from app.services.common import (
    audit,
    is_owner,
    require_owner,
    sold_quantity,
    transaction,
)


class OrderService:
    def __init__(self, engine: Engine, max_qty_per_item: int | None = None) -> None:
        self.engine = engine
        self.maximum = (
            int(os.environ.get("MAX_QTY_PER_ITEM", "20"))
            if max_qty_per_item is None
            else max_qty_per_item
        )
        if type(self.maximum) is not int or self.maximum < 1:
            raise ValueError("MAX_QTY_PER_ITEM must be a positive integer")

    def create_draft(self, sender: str, note: str | None = None) -> int:
        with transaction(self.engine) as db:
            current = db.scalar(select(POSession).where(POSession.status == "OPEN"))
            if current is None:
                raise ValueError("No OPEN session")
            customer = db.scalar(select(Customer).where(Customer.phone_e164 == sender))
            if customer is None:
                customer = Customer(phone_e164=sender)
                db.add(customer)
                db.flush()
            order = Order(session_id=current.id, customer_id=customer.id, note=note)
            db.add(order)
            db.flush()
            if is_owner(db, sender):
                audit(
                    db,
                    sender,
                    "create_draft",
                    None,
                    {"order_id": order.id, "session_id": current.id, "note": note},
                )
            return order.id

    def _own_order(self, db: Session, sender: str, order_id: int) -> Order:
        order = db.scalar(
            select(Order)
            .join(Customer)
            .where(Order.id == order_id, Customer.phone_e164 == sender)
        )
        if order is None:
            raise PermissionError("Order does not belong to sender")
        return order

    def _open_draft(self, db: Session, order: Order) -> POSession:
        current = db.get(POSession, order.session_id)
        if order.status != "DRAFT" or current is None or current.status != "OPEN":
            raise ValueError(
                "Only drafts in an OPEN session can be edited or confirmed"
            )
        return current

    def set_item(
        self, sender: str, order_id: int, product_id: int, quantity: int
    ) -> None:
        validate_quantity(quantity, self.maximum)
        with transaction(self.engine) as db:
            order = self._own_order(db, sender, order_id)
            self._open_draft(db, order)
            self._available(db, order.session_id, product_id)
            item = db.scalar(
                select(OrderItem).where(
                    OrderItem.order_id == order_id, OrderItem.product_id == product_id
                )
            )
            before = None if item is None else {"quantity": item.quantity}
            if item is None:
                db.add(
                    OrderItem(
                        order_id=order_id, product_id=product_id, quantity=quantity
                    )
                )
            else:
                item.quantity = quantity
            if is_owner(db, sender):
                audit(
                    db,
                    sender,
                    "set_item",
                    before,
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "quantity": quantity,
                    },
                )

    def remove_item(self, sender: str, order_id: int, product_id: int) -> None:
        with transaction(self.engine) as db:
            order = self._own_order(db, sender, order_id)
            self._open_draft(db, order)
            item = db.scalar(
                select(OrderItem).where(
                    OrderItem.order_id == order_id, OrderItem.product_id == product_id
                )
            )
            if item is not None:
                if is_owner(db, sender):
                    audit(
                        db,
                        sender,
                        "remove_item",
                        {
                            "order_id": order_id,
                            "product_id": product_id,
                            "quantity": item.quantity,
                        },
                        None,
                    )
                db.delete(item)

    def _available(
        self, db: Session, session_id: int, product_id: int
    ) -> tuple[Product, SessionProduct]:
        product = db.get(Product, product_id)
        attached = db.get(SessionProduct, (session_id, product_id))
        if product is None or attached is None or not product.is_active:
            raise ValueError("Product unavailable in this session")
        return product, attached

    def _summary(self, db: Session, order: Order) -> OrderSummary:
        current = db.get(POSession, order.session_id)
        assert current is not None
        items: list[SummaryItem] = []
        for item, product in db.execute(
            select(OrderItem, Product)
            .join(Product)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.id)
        ):
            price = (
                product.price_idr if order.status == "DRAFT" else item.unit_price_idr
            )
            if price is None:
                # Cancelled drafts have no confirmation snapshot.
                price = product.price_idr
            items.append(
                SummaryItem(
                    product.id,
                    product.name,
                    item.quantity,
                    price,
                    item.quantity * price,
                )
            )
        return OrderSummary(
            order.id,
            order.session_id,
            order.status,
            tuple(items),
            sum(item.line_total_idr for item in items),
            current.notes,
        )

    def show_cart(self, sender: str, order_id: int) -> OrderSummary:
        with Session(self.engine) as db:
            return self._summary(db, self._own_order(db, sender, order_id))

    def confirm_order(
        self, sender: str, order_id: int, total_seen: int
    ) -> OrderSummary:
        validate_money(total_seen)
        with transaction(self.engine) as db:
            order = self._own_order(db, sender, order_id)
            if order.status in ("CONFIRMED", "PAID", "FULFILLED"):
                return self._summary(db, order)
            self._open_draft(db, order)
            summary = self._summary(db, order)
            if not summary.items:
                raise ValueError("Cannot confirm an empty draft")
            if total_seen != summary.total_idr:
                raise PriceMismatch(summary)
            items = list(
                db.scalars(select(OrderItem).where(OrderItem.order_id == order_id))
            )
            for item in items:
                validate_quantity(item.quantity, self.maximum)
                product, attached = self._available(
                    db, order.session_id, item.product_id
                )
                sold = sold_quantity(db, order.session_id, item.product_id)
                if attached.quota is not None and sold + item.quantity > attached.quota:
                    raise ValueError("Insufficient quota")
                item.unit_price_idr = product.price_idr
            order.total_idr = summary.total_idr
            order.status = "CONFIRMED"
            if is_owner(db, sender):
                audit(
                    db,
                    sender,
                    "confirm_order",
                    {"order_id": order_id, "status": "DRAFT"},
                    {
                        "order_id": order_id,
                        "status": order.status,
                        "total_idr": order.total_idr,
                    },
                )
            db.flush()
            return self._summary(db, order)

    def cancel_order(self, sender: str, order_id: int) -> None:
        with transaction(self.engine) as db:
            owner = is_owner(db, sender)
            order = (
                db.get(Order, order_id)
                if owner
                else self._own_order(db, sender, order_id)
            )
            if order is None:
                raise ValueError("Unknown order")
            current = db.get(POSession, order.session_id)
            assert current is not None
            target = transition_order(
                order.status,
                "CANCELLED",
                owner=owner,
                session_open=current.status == "OPEN",
            )
            before = {"order_id": order.id, "status": order.status}
            order.status = target
            if owner:
                audit(
                    db,
                    sender,
                    "cancel_order",
                    before,
                    {"order_id": order.id, "status": target},
                )

    def set_order_status(self, sender: str, order_id: int, target: str) -> None:
        with transaction(self.engine) as db:
            require_owner(db, sender)
            order = db.get(Order, order_id)
            if order is None:
                raise ValueError("Unknown order")
            destination = transition_order(
                order.status, target, owner=True, session_open=False
            )
            before = {"order_id": order.id, "status": order.status}
            order.status = destination
            audit(
                db,
                sender,
                "order_status",
                before,
                {"order_id": order.id, "status": destination},
            )
