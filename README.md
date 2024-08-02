# Sorteia
Goal: allow arbitrary sorting instead of attribute-based sorting.

- 1 document per user per resource = `CustomSorting`.
  - Allow multiple users to sort the same documents differently.
  - Allow for a large number of items to be sorted.

You can use it as a route dependency to use it on your API or use it directly on your code using the raw methods from the slass `Sortings`.

```python
class CustomSorting(BaseModel):
    id: PyObjectId = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: Infostar
    position: int
    resource_collection: str 
    resource_id: PyObjectId
```

## Installation:
From repo:
```sh
pip install -e ./
```
From `pypi`:
```sh
pip install sorteia
```

## Class Sortings
Contains the core operations used to sort the elements. Elements always filtered by the infostar `user_handle` and `authprovider_org`. 

> When initializing the class, pass as arguments `collection_name`, `alias` and `db_name`. 

#### reorder_one
Reorders a resource in the custom order by upserting a `CustomSorting` object. If you send `-1` the position will be set as the `max_position` (as the last document in the collection)
> Returns: `ReorderOneUpsertedOut` | `ReorderOneUpdatedOut`

#### reorder_many
Reorders many resources in the custom order sent as body.
> Returns: `BulkWriteResult`

#### read_many
Returns the `CustomSorting` objects in the positions order.
> Returns: `list[CustomSorting]`

#### read_many_whole_object
Returns the `CustomSorting` object with the whole object as an attribute named resource ($lookup), in the order they were sorted.
> Returns: `list[CustomSortingWithResource[T]]`

#### read_many_entire_collection
Returns all of the objects (the ordered and not ordered as well) in the order they were sorted. The objects that have not been ordered yet (don't have a custom-sorting document associated with) will be inserted at the end of the list (sorted by the created_at date, in descending order).
> Returns: `CommandCursor[Any]` 

#### delete_one
Delete a resource from the custom order using the `resource_id` as reference. 
> Returns: `DeleteResult`

#### read_all_ordered_objects
Reads the objects in order - reads the objects that do not have the custom order and the ones who has it. It loads all of the objects into memory (not recommended).
> Returns: `list[T]`

### Example of raw use:
```python
# can initiate Sortings with or without alias and db_name
Sortings(
        collection_name=resource, alias=org, db_name=org
    ).reorder_one(
        creator=creator,
        resource_id=body.resource_id,
        position=position,
        background_task=background_task,
    )

Sortings(collection_name=resource).delete_one(
        resource_id, creator, background_task
      )
```
All of the Sortings class methods work the same way, by initiating a Sortings object and calling any available method.


## How to use the route dependencies on an API:
#### 1. Create the `indexes` that are required to perform search operations later.
```python
from sorteia.operations import Sortings

# create search index
Sortings.create_search_indexes(
    mongo_uri=DB.get_client(alias=alias).HOST,
    db_name=DB.get(alias=alias).name,
)
```

#### 2. Initialize the routes dependencies using the method `add_sorting_resources_dependency()` as seen below.
```python
from sorteia.dependencies import sorting_resources

# include route dependencies
router = APIRouter(prefix="/api")
sorting_resources.add_sorting_resources_dependency(app)
```
> [!NOTE]
> With that command, the following routes will be included to the api:
> - get_sortings
> - reorder_one
> - reorder_many
> - delete_sorting


#### 3. Adapt your desired `/GET` operations to return the custom sorted documents. 
```python
from sortings.operations import Sortings

sortings = Sortings(
    collection_name="collection_name", alias=org, db_name=org
)

filtering = { 
    "name": "testing"
}
result = sortings.read_many_entire_collection(
    infostar=infostar,
    offset=offset,
    limit=limit,
    projection=projection,
    **filtering,
)
```
> [!TIP]
> For each new document created in the desired collection (that will be custom sorted at some point), create a new sorting with position set as `-1`, so the document will have the last position in the list, and will be easier to perform reorder operations later.