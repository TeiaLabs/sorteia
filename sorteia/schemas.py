from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from tauth.schemas import Infostar

from redbaby.pyobjectid import PyObjectId

T = TypeVar("T")


class ReorderManyResourcesIn(BaseModel):
    resource_id: PyObjectId
    resource_ref: str
    position: int


class ReorderManyResourcesInList(BaseModel):
    resources: list[ReorderManyResourcesIn]


class ReorderOneResourceIn(BaseModel):
    resource_id: PyObjectId


class ReorderOneUpsertedOut(BaseModel):
    id: PyObjectId
    created_at: datetime
    updated_at: datetime
    created_by: Infostar


class ReorderOneUpdatedOut(BaseModel):
    id: PyObjectId
    updated_at: datetime


class CustomSortingWithResource(BaseModel, Generic[T]):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Infostar
    position: int
    resource_id: PyObjectId
    resource: T  # actual resource
