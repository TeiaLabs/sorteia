# Sorteia

## Models
```python
class CustomSorting(BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource_collection: str 
    resource_id: PyObjectId

class CustomSortingWithResource(Generic[T], BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource: T  # actual resource
```
Observation: `resource_collection` and `resource_id` used to be DBRef, but its attributes made it hard to read from database.

## Schemas 
### In
```python
class ReorderManyResourcesIn(BaseModel):
    resource_id: PyObjectId
    resource_ref: str
    position: int

class ReorderOneResourceIn(BaseModel):
    resource_id: PyObjectId
```

#### Examples
`ReorderManyResourcesIn`: 
```python
{ 
    "resource_id": "resource.$id",
    "resource_ref": "resource.$ref",
    "position": 0,
}
```

`ReorderOneResourceIn`:
```python
{"resource_id": "pyobjectid"}
```

### Out
```python
class ReorderOneUpsertedOut(BaseModel):
    id: PyObjectId
    created_at: datetime
    updated_at: datetime
    created_by: Creator


class ReorderOneUpdatedOut(BaseModel):
    id: PyObjectId
    updated_at: datetime
```