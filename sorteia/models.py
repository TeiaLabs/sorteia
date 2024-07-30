from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from tauth.schemas import Infostar

from redbaby.pyobjectid import PyObjectId


class CustomSorting(BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Infostar
    position: int
    resource_collection: str
    resource_id: PyObjectId
