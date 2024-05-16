from datetime import datetime

from pydantic import BaseModel, Field
from tauth.schemas import Creator  # type: ignore

from sorteia.utils import PyObjectId


class DBRef(BaseModel):
    collection: str = Field(alias="$ref")
    id: PyObjectId = Field(alias="$id")

    # class Config:
    #   populate_by_name = True
    #   json_encoders = {PyObjectId: lambda oid: str(oid)}


class CustomSorting(BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource_ref: DBRef
    # id: Hash(created_by.user_email, resource_ref.$ref, position)
    # indexes = [{"resource_ref.$ref": 1, "position": 1}]


class CustomSortingWithResource[T](BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource: T  # actual resource
