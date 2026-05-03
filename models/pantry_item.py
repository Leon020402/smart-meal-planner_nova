import uuid
from datetime import date


class PantryItem:
    """Represents an ingredient stored in the user's pantry."""

    EXPIRY_WARNING_DAYS = 3
    UNIT_OPTIONS = ["g", "kg", "ml", "L", "pcs", "tbsp", "tsp", "cup", "oz", "lb"]

    def __init__(
        self,
        name: str,
        quantity: float,
        unit: str,
        expiration_date: str = None,   # ISO string "YYYY-MM-DD" or None
        item_id: str = None,
    ):
        self.id = item_id if item_id else str(uuid.uuid4())
        self.name = name
        self.quantity = float(quantity)
        self.unit = unit
        self.expiration_date = expiration_date

    # ── Expiry helpers ─────────────────────────────────────────────────────────

    def _expiry_date(self):
        """Return a date object or None."""
        if not self.expiration_date:
            return None
        try:
            return date.fromisoformat(self.expiration_date)
        except ValueError:
            return None

    def is_expired(self) -> bool:
        exp = self._expiry_date()
        return exp is not None and exp < date.today()

    def is_expiring_soon(self) -> bool:
        exp = self._expiry_date()
        if exp is None:
            return False
        days = (exp - date.today()).days
        return 0 <= days <= self.EXPIRY_WARNING_DAYS

    def days_until_expiry(self):
        """Return number of days until expiry, or None if no date set."""
        exp = self._expiry_date()
        if exp is None:
            return None
        return (exp - date.today()).days

    # ── Serialisation ──────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "expiration_date": self.expiration_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PantryItem":
        return cls(
            name=data["name"],
            quantity=data.get("quantity", 0.0),
            unit=data.get("unit", "g"),
            expiration_date=data.get("expiration_date"),
            item_id=data.get("id"),
        )

    def __repr__(self) -> str:
        return f"PantryItem(name={self.name!r}, qty={self.quantity} {self.unit})"
