from datetime import datetime

from pydantic import BaseModel
from tauth.schemas import Creator  # type: ignore

from sorteia.utils import PyObjectId


class ReorderManyResourcesIn(BaseModel):
    resource_id: PyObjectId
    resource_ref: str
    position: int

    class Config:
        examples = {
            "reorder-many": {
                "value": [
                    {
                        "resource_id": "resource.$id",
                        "resource_ref": "resource.$ref",
                        "position": 0,
                    },
                    {
                        "resource_id": "resourceid2",
                        "resource_ref": "resourceref2",
                        "position": 1,
                    },
                ]
            }
        }


class ReorderOneResourceIn(BaseModel):
    resource_id: PyObjectId

    class Config:
        examples = {"reorder-one": {"value": {"resource_id": "pyobjectid"}}}


class ReorderOneUpsertedOut(BaseModel):
    id: PyObjectId
    created_at: datetime
    updated_at: datetime
    created_by: Creator


class ReorderOneUpdatedOut(BaseModel):
    id: PyObjectId
    updated_at: datetime
