class CustomOrderNotSaved(Exception):
    """Document containing custom order and document to be ordered could not be saved"""


class CustomOrderNotFound(Exception):
    """Document containing custom order not found"""


class ObjectToBeSortedNotFound(Exception):
    """Object to be sorted was not found"""
