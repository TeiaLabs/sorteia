from pydantic import Field
import datetime
from bson import ObjectId
from tauth.schemas import Creator

class DBRef:
  collection: str = Field(alias="$ref") 
  id: ObjectId = Field(alias="$id")

  class Config: 
    allow_population_by_field_name = True
    json_encoders = {ObjectId: lambda oid: str(oid)}


class CustomSorting:
  # id: Hash(created_by.user_email, resource_ref.$ref, position)
  created_at: datetime
  updated_at: datetime
  created_by: Creator
  position: int
  resource_ref: DBRef
                
  indexes = [{"resource_ref.$ref": 1, "position": 1}] 

class CustomSortingWithResource[T]: 
  id: ObjectId
  created_at: datetime
  updated_at: datetime
  created_by: Creator
  position: int
  resource: T #actual resource