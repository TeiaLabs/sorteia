from typing import Any


class CustomOrderNotSaved(Exception):
    """Document containing custom order and document to be ordered could not be saved"""


class CustomOrderNotFound(Exception):
    """Document containing custom order not found"""


class ObjectToBeSortedNotFound(Exception):
    """Object to be sorted was not found"""


class PositionOutOfBounds(Exception):
    """Position is out of bounds"""

    def __init__(
        self, message: str = "An error occurred", detail: dict[str, Any] | None = None
    ):
        self.message = message
        self.detail = detail
        super().__init__(self.message)
