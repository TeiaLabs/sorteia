from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from tauth.schemas import Creator  # type: ignore

from sorteia.utils import PyObjectId

T = TypeVar("T")


class DBRef(BaseModel):
    collection: str = Field(alias="$ref")
    id: PyObjectId = Field(alias="$id")


class CustomSorting(BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource_ref: DBRef


class CustomSortingWithResource(Generic[T], BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource: T  # actual resource
