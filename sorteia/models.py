from typing import Any, Collection, Optional
from pymongo import IndexModel
from redbaby.document import Document
from .schemas import CustomSorting, CustomSortingWithResource
from redbaby.database import DB

class CustomSortingDAO(Document, CustomSorting):
    @classmethod
    def collection_name(cls) -> str:
        return "custom-sortings"

    @classmethod
    def collection(cls, suffix: Optional[str] = None) -> Collection:
        return DB.get(suffix=suffix)[cls.collection_name()]

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        return [{"resource_ref.$ref": 1, "position": 1}]

    def bson(self) -> dict[str, Any]:
        obj = self.model_dump(by_alias=True)
        return obj
    