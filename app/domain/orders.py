from dataclasses import dataclass


def validate_quantity(quantity: int, maximum: int) -> None:
    if type(quantity) is not int or not 1 <= quantity <= maximum:
        raise ValueError(f"Quantity must be an integer between 1 and {maximum}")


def validate_money(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("Money must be nonnegative integer rupiah")


@dataclass(frozen=True)
class SummaryItem:
    product_id: int
    name: str
    quantity: int
    unit_price_idr: int
    line_total_idr: int


@dataclass(frozen=True)
class OrderSummary:
    order_id: int
    session_id: int
    status: str
    items: tuple[SummaryItem, ...]
    total_idr: int
    pickup_info: str | None


class PriceMismatch(ValueError):
    def __init__(self, summary: OrderSummary) -> None:
        super().__init__("Price changed; show fresh summary before confirming")
        self.summary = summary
