import os
from datetime import datetime
from typing import Any, Set, Type, TypeVar

import pymongo
import pymongo.command_cursor
import pymongo.cursor
import pymongo.results
from dotenv import find_dotenv, load_dotenv
from fastapi import BackgroundTasks
from loguru import logger
from redbaby.database import DB
from tauth.schemas import Infostar

from .exceptions import (
    CustomOrderNotFound,
    CustomOrderNotSaved,
    ObjectToBeSortedNotFound,
    PositionOutOfBounds,
)
from .models import CustomSorting
from .schemas import (
    CustomSortingWithResource,
    ReorderManyResourcesIn,
    ReorderOneUpdatedOut,
    ReorderOneUpsertedOut,
)
from redbaby.pyobjectid import PyObjectId

load_dotenv(find_dotenv())

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# db connection to add custom sortings
DB.add_conn(
    db_name=DB_NAME,  # type: ignore
    uri=MONGO_URI,  # type: ignore
    alias="default",
    start_client=True,
)

T = TypeVar("T")


class Sortings:
    """Operations to manipulate custom ordered objects.

    Allows arbitrary sorting instead of attribute-based sorting.
    First position = 0, second position = 1, and so on.
    Works based on the following assumptions:
    - 1 document per user per resource.
    - Allow multiple users to sort the same documents differently.
    - Allow for a large number of items to be sorted.
    To get all of the objects on the correct custom order, the client
    must run `read_all_ordered_objects` that returns a list of the
    model passed as parameter.

    Model saved on the database:
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

    """

    def __init__(
        self,
        collection_name: str,
        alias: str = "default",
        db_name: str = DB_NAME,  # type: ignore
    ):
        """Initializes the object to use its core operations.

        Initializes the Sortings object so the client can manipulate custom
        ordered objects. Saves the custom ordered objetcs on a collection
        named `custom-sortings` on the same database as the collection to be sorted.
        This database will be determined by the `alias` and `db_name` parameters.

        Args:
            collection_name (str): collection name of the elements to be sorted
            alias (str, optional): alias of the database connection, default is `default`
            db_name (str, optional): name of the database, if not, it will get from env variables (`DB_NAME`)
        """

        logger.debug(f"Initializing Sortings for {collection_name}")
        self.collection: str = collection_name
        self.database = DB.get(alias=alias, db_name=db_name)
        self.sortings = self.database["custom-sortings"]
        logger.debug(
            f"Object sortings created for {collection_name} - {self.database.name}"
        )

    def reorder_one(
        self,
        infostar: Infostar,
        resource_id: PyObjectId,
        position: int,
        background_task: BackgroundTasks | None,
    ) -> ReorderOneUpsertedOut | ReorderOneUpdatedOut:
        """Reorders a resource in the custom order.

        Args:
            creator(Creator): Creator object
            resource_id(PyObjectId): ObjectId of the resource to be ordered
            position(int): position to be set (0 is the first position)

        Returns:
            The object that was reordered and updated or inserted on the collection.

        Raises:
            ObjectToBeSortedNotFound: if the object to be sorted does not exist on the targeted collection.
            CustomOrderNotSaved: if the custom order could not be saved - maybe because of an internal error.
            PostionOutOfBounds: if the position is out of bounds.
        """

        # check if user is owner of that resource to reorder it
        logger.debug(f"Searching for object to be sorted on {self.collection}")
        object_sorted = self.database[self.collection].find_one(
            filter={
                "_id": resource_id,
                "created_by.user_handle": infostar.user_handle,
                "created_by.authprovider_org": infostar.authprovider_org,
            }
        )
        if object_sorted is None:
            raise ObjectToBeSortedNotFound
        logger.debug("Object to be sorted found")

        max_position: int = (
            self.database[self.collection].count_documents(
                filter={
                    "created_by.user_handle": infostar.user_handle,
                    "created_by.authprovider_org": infostar.authprovider_org,
                }
            )
            - 1  # position start at 0
        )
        # last position
        if position == -1:
            position = max_position

        if position > max_position or position < 0:
            raise PositionOutOfBounds(
                message=f"Position out of bounds: {position} cannot be bigger than {max_position}",
                detail={
                    "max_position": max_position,
                    "position": position,
                },
            )
        logger.debug(f"Position is within bounds - bound: {max_position}")

        filter = {
            "resource_collection": self.collection,
            "resource_id": resource_id,
            "created_by.user_handle": infostar.user_handle,
            "created_by.authprovider_org": infostar.authprovider_org,
        }
        logger.debug(f"Filter to search for the object to be sorted created: {filter}")

        updated_at = datetime.now()
        created_at = datetime.now()
        custom_sorting = {
            "position": position,
            "resource_collection": self.collection,
            "resource_id": resource_id,
            "updated_at": updated_at,
        }
        update = {
            "$set": custom_sorting,
            "$setOnInsert": {
                "created_at": created_at,
                "created_by": infostar.model_dump(by_alias=True),
            },
        }

        result = self.sortings.update_one(
            filter=filter,
            update=update,
            upsert=True,
        )
        logger.debug(
            f"Object sorted updated or inserted on the custom sortings collection: {result}"
        )

        if result.upserted_id is not None:
            result = ReorderOneUpsertedOut(
                id=result.upserted_id,
                created_at=created_at,
                updated_at=updated_at,
                created_by=infostar,
            )
        elif result.modified_count == 1 or result.matched_count == 1:
            object = self.sortings.find_one(filter=filter)
            if object is None:
                raise CustomOrderNotSaved
            result = ReorderOneUpdatedOut(
                id=object["_id"],
                updated_at=updated_at,
            )
        else:
            raise CustomOrderNotSaved

        if background_task:
            logger.debug("Background task to update the other objects positions")
            background_task.add_task(
                self.sortings.update_many,
                filter={
                    "position": {"$gt": position},
                    "resource_collection": self.collection,
                    "created_by.user_handle": infostar.user_handle,
                    "created_by.authprovider_org": infostar.authprovider_org,
                },
                update={"$inc": {"position": 1}},
            )
        return result

    def reorder_many(
        self,
        resources: list[ReorderManyResourcesIn],
        infostar: Infostar,
    ) -> pymongo.results.BulkWriteResult:
        """Reorders many resources in the custom order sent as body.

        Type of body to send as `resources`:
        ```
        [{
            "resource_id": "resource.$id",
            "resource_ref": "resource.$ref",
            "position": 0,
        }]
        ```
        WARNING: sent `ids` are not checked if they exist on the collection
        to be sorted because of the many different searches on the database necessary.
        Make sure to check it before sending the request.

        Args:
            resources(list[ReorderManyResourcesIn]): resources to be reordered.
            creator(Creator): Creator object.

        Returns:
            BulkWriteResult object from pymongo.

        Raises:
            PositionOutOfBounds: if the position is out of bounds.

        """
        max_position: int = self.database[self.collection].count_documents(
            filter={
                "created_by.user_handle": infostar.user_handle,
                "created_by.authprovider_org": infostar.authprovider_org,
            }
        )
        for resource in resources:
            if resource.position > max_position or resource.position < 0:
                raise PositionOutOfBounds(
                    message="Position out of bounds - position cannot be higher than the total amount of elements to be sorted.",
                    detail={
                        "max_position": max_position,
                        "position": resource.position,
                    },
                )

        result = self.sortings.bulk_write(
            [
                pymongo.UpdateOne(
                    filter={
                        "resource_collection": self.collection,
                        "resource_id": resource.resource_id,
                        "created_by.user_handle": infostar.user_handle,
                        "created_by.authprovider_org": infostar.authprovider_org,
                    },
                    update={
                        "$set": {
                            "position": resource.position,
                            "updated_at": datetime.now(),
                        },
                        "$setOnInsert": {
                            "created_at": datetime.now(),
                            "created_by": infostar.model_dump(by_alias=True),
                        },
                    },
                    upsert=True,
                )
                for resource in resources
            ]
        )
        return result

    def read_many(
        self,
        infostar: Infostar,
    ) -> list[CustomSorting]:
        """Returns the objects in the order they were sorted.

        Args:
            creator(Creator): Creator object.

        Returns:
            a list of CustomSorting objects.
        """
        # TODO: change this Any to specific type
        custom_sortings: pymongo.cursor.Cursor[Any] = self.sortings.find(
            filter={
                "resource_collection": self.collection,
                "created_by.user_handle": infostar.user_handle,
                "created_by.authprovider_org": infostar.authprovider_org,
            }
        ).sort("position", pymongo.ASCENDING)

        return list(custom_sortings)

    def read_many_whole_object(
        self,
        infostar: Infostar,
    ) -> list[CustomSortingWithResource[T]]:
        """Returns the objects in the order they were sorted.

        Args:
            creator(Creator): Creator object.

        Returns:
            a list of CustomSortingWithResource objects.
        """
        # TODO: change this Any to specific type
        custom_sortings: pymongo.command_cursor.CommandCursor[Any] = (
            self.sortings.aggregate(
                [
                    {
                        "$match": {
                            "resource_collection": self.collection,
                            "created_by.user_handle": infostar.user_handle,
                            "created_by.authprovider_org": infostar.authprovider_org,
                        }
                    },
                    {
                        "$lookup": {
                            "from": self.collection,
                            "localField": "resource_id",
                            "foreignField": "_id",
                            "as": "resource",
                        }
                    },
                    {
                        "$unwind": {
                            "path": "$resource",
                            "preserveNullAndEmptyArrays": True,
                        }
                    },
                    {
                        "$project": {
                            "resource._id": 0,
                        }
                    },
                    {"$sort": {"position": pymongo.ASCENDING}},
                ]
            )
        )
        return list(custom_sortings)

    def delete_one(
        self, position: int, infostar: Infostar, background_task: BackgroundTasks | None
    ) -> pymongo.results.DeleteResult:
        """Deletes a resource from the custom order according to the position.

        Args:
            position(int): position to be deleted.
            creator(Creator): Creator object.
            background_task(BackgroundTasks): send None to not update the other objects positions after deletion.

        Raises:
            CustomOrderNotFound: if the custom order could not be found to be deleted.
        """
        user_email = infostar.user_handle

        filter = {
            "position": position,
            "created_by.user_handle": user_email,
            "created_by.authprovider_org": infostar.authprovider_org,
        }
        result: pymongo.results.DeleteResult = self.sortings.delete_one(filter)

        if result.deleted_count == 0:
            raise CustomOrderNotFound

        if background_task is not None:
            background_task.add_task(
                self.sortings.update_many,
                filter={
                    "position": {"$gt": position},
                    "resource_collection": self.collection,
                    "created_by.user_handle": user_email,
                    "created_by.authprovider_org": infostar.authprovider_org,
                },
                update={"$inc": {"position": -1}},
            )
        return result

    def read_all_ordered_objects(
        self, infostar: Infostar, model: Type[T], **filters
    ) -> list[T]:
        """Reads all objects from the collection already sorted by the custom order.

        Args:
            creator(Creator): Creator object.
            model(Type[T]): Pydantic model to be used to create the objects.
            **filters: filters to be applied to the find query on the `model` collection.
        """
        query: dict[str, Any] = {k: v for k, v in filters.items() if v is not None}

        logger.debug(f"Searching for objects in the collection {self.collection}")
        unordered_objs: pymongo.cursor.Cursor[Any] = self.database[
            self.collection
        ].find(query)
        unordered_objs_list = list(unordered_objs)
        logger.debug(
            f"Found {len(unordered_objs_list)} objects in the original collection"
        )

        sorted_objs: list[CustomSortingWithResource[T]] = self.read_many_whole_object(
            infostar
        )
        logger.debug(f"Found {len(sorted_objs)} objects of these already sorted")

        custom_sortings_set: Set[PyObjectId] = {
            obj["resource_id"] for obj in sorted_objs
        }
        filtered_objs: list[model] = [
            obj for obj in unordered_objs_list if obj["_id"] not in custom_sortings_set
        ]
        logger.debug(
            f"There are now {len(filtered_objs)} objects that are not repeated ids"
        )

        for sorting in sorted_objs:
            obj = model(**sorting["resource"], _id=sorting["resource_id"])  # type: ignore
            filtered_objs.insert(sorting["position"], obj)

        return filtered_objs

    @classmethod
    def create_search_indexes(cls, mongo_uri: str, db_name: str) -> None:
        """Creates the indexes needed for the custom sortings.

        Args:
            mongo_uri(str): URI to connect to the MongoDB database.
            db_name(str): name of the database to create the indexes.
        """
        logger.debug("Creating indexes for custom sortings")
        client = pymongo.MongoClient(mongo_uri)
        db = client[db_name]
        db["custom-sortings"].create_index([("resource_collection", pymongo.ASCENDING)])
        db["custom-sortings"].create_index([("position", pymongo.ASCENDING)])
