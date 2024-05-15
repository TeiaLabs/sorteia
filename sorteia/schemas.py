from pydantic import BaseModel

from sorteia.utils import PyObjectId

class ReorderResourcesIn(BaseModel):
  resource_id: PyObjectId
  resource_ref: str 
  position: int
