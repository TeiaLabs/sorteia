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
```
_Observation:_ `resource_collection` and `resource_id` used to be a DBRef, but its attributes made it hard to read from database.

## Schemas - In
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
[
    { 
        "resource_id": "resource.$id",
        "resource_ref": "resource.$ref",
        "position": 0,
    },
    { 
        "resource_id": "resource.$id2",
        "resource_ref": "resource.$re2",
        "position": 2,
    },
]
```

`ReorderOneResourceIn`:
```python
{"resource_id": "pyobjectid"}
```

## Schemas - Out
```python
class ReorderOneUpsertedOut(BaseModel):
    id: PyObjectId
    created_at: datetime
    updated_at: datetime
    created_by: Creator

class ReorderOneUpdatedOut(BaseModel):
    id: PyObjectId
    updated_at: datetime

class CustomSortingWithResource(Generic[T], BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Creator
    position: int
    resource_id: PyObjectId
    resource: T  # actual resource
```


## Class Sortings
Contains the core operations used to order the elements. Elements always filtered by the creator. 
When initializing the class, pass as arguments `collection_name`, `alias` and `db_name`: 

### reorder_one
Reorders a resource in the custom order by upserting a `CustomSorting` object.
Out: `ReorderOneUpsertedOut` | `ReorderOneUpdatedOut`

### reorder_many
Reorders many resources in the custom order sent as body.
Out: `BulkWriteResult`

### read_many
Returns the `CustomSorting` objects in the positions order.
Out: `list[CustomSorting]`

### read_many_whole_object
Returns the `CustomSorting` object with the whole object as an attribute named resource ($lookup), in the order they were sorted.
Out: `list[CustomSortingWithResource[T]]`

### delete_one
Delete a resource from the custom order according to the position. 
Out: `DeleteResult`

### read_all_ordered_objects
Reads the objects in order - reads the objecs that do not have the custom order and the ones who has it.
Out: `list[model]`
 
## Exceptions
CustomOrderNotSaved - reorders
ObjectToBeSortedNotFound - reorders
PositionOutOfBounds - reorders

CustomOrderNotFound - delete

## Routes dependencies
First of all, call `create_search_indexes` passing as arguments `mongo_uri` and `db_name` to create the indexes on the correct database.


## Examples of use
```python
from sorteia.operations import Sortings

# create search index
Sortings.create_search_indexes(
    mongo_uri=DB.get_client(alias=alias).HOST,
    db_name=DB.get(alias=alias).name,
)

# include route dependencies
router = APIRouter(prefix="/api")
sorting_resources.add_sorting_resources_dependency(app)

# check athena v2 docs - canvases
```
