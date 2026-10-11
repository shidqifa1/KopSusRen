from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.engine import Engine

from app.db.models import Customer, Message
from app.services.common import transaction


@dataclass(frozen=True)
class InboundResult:
    message_id: int
    duplicate: bool


class MessageService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def record_inbound_message(
        self, provider_message_id: str, sender: str, text: str
    ) -> InboundResult:
        if not provider_message_id:
            raise ValueError("Provider message ID is required")
        with transaction(self.engine) as db:
            existing = db.scalar(
                select(Message).where(
                    Message.provider_message_id == provider_message_id
                )
            )
            if existing is not None:
                return InboundResult(existing.id, duplicate=True)
            customer = db.scalar(select(Customer).where(Customer.phone_e164 == sender))
            if customer is None:
                customer = Customer(phone_e164=sender)
                db.add(customer)
                db.flush()
            message = Message(
                provider_message_id=provider_message_id,
                direction="in",
                customer_id=customer.id,
                text=text,
            )
            db.add(message)
            db.flush()
            return InboundResult(message.id, duplicate=False)
