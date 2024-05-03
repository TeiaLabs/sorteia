import datetime
from tauth.schemas import Creator

class CustomSorting:
#   id: Hash(created_by.user_email, resource_ref.$ref, position)
  created_at: datetime
  updated_at: datetime
  created_by: Creator
  position: int
#   resource_ref: {$ref, $id}  # DBRef

  indexes = [{"resource_ref.$ref": 1, "position": 1}]