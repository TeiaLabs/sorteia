import os
from datetime import datetime
from typing import Any

import pymongo
import pymongo.command_cursor
import pymongo.cursor
import pymongo.results
from annotated_types import T
from dotenv import load_dotenv
from fastapi import BackgroundTasks
from loguru import logger
from redbaby.database import DB  # type: ignore
from tauth.schemas import Creator  # type: ignore

from .exceptions import (
    CustomOrderNotFound,
    CustomOrderNotSaved,
    ObjectToBeSortedNotFound,
)
from .models import CustomSorting, CustomSortingWithResource
from .schemas import ReorderManyResourcesIn, ReorderOneUpdatedOut, ReorderOneUpsertedOut
from .utils import PyObjectId  # type: ignore

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# db connection to add custom sortings
DB.add_conn(
    db_name=DB_NAME,
    uri=MONGO_URI,
    # alias="default",
    start_client=True,
)


class Sortings:

    def __init__(self, collection_name: str):
        """
        Initializes the Sortings object so the client can manipulate custom ordered objects. Saves the custom ordered objetcs on a collection named `custom-sortings` on the same database as the collection to be sorted.
        `collection_name`: collection name of the elements to be sorted
        """
        logger.debug(f"Initializing Sortings for {collection_name}")
        self.collection: str = collection_name
        self.sortings = DB.get()["custom-sortings"]
        self.create_search_indexes()

    def reorder_one(
        self, creator: Creator, resource_id: PyObjectId, position: int
    ) -> ReorderOneUpsertedOut | ReorderOneUpdatedOut:
        """
        Reorders a resource in the custom order.
        `creator`: Creator object
        `resource_id`: ObjectId of the resource to be ordered
        `position`: int position to be set
        """

        # check if user is owner of that resource to reorder it
        object_sorted = DB.get()[self.collection].find_one(
            filter={"_id": resource_id, "created_by.user_email": creator.user_email}
        )
        if object_sorted is None:
            raise ObjectToBeSortedNotFound

        filter = {
            "resource_ref": {"$ref": self.collection, "$id": resource_id},
            "created_by.user_email": creator.user_email,
        }

        updated_at = datetime.now()
        created_at = datetime.now()
        custom_sorting = {
            "position": position,
            "resource_ref": {"$ref": self.collection, "$id": resource_id},
            "updated_at": updated_at,
        }
        update = {
            "$set": custom_sorting,
            "$setOnInsert": {
                "created_at": created_at,
                "created_by": creator.model_dump(by_alias=True),
            },
        }

        result = self.sortings.update_one(
            filter=filter,
            update=update,
            upsert=True,
        )

        if result.upserted_id is not None:
            return ReorderOneUpsertedOut(
                id=result.upserted_id,
                created_at=created_at,
                updated_at=updated_at,
                created_by=creator,
            )
        elif result.modified_count == 1 or result.matched_count == 1:
            object = self.sortings.find_one(filter=filter)
            if object is None:
                raise CustomOrderNotSaved
            return ReorderOneUpdatedOut(
                id=object["_id"],
                updated_at=updated_at,
            )
        else:
            raise CustomOrderNotSaved

    def reorder_many(
        self,
        resources: list[ReorderManyResourcesIn],
        creator: Creator,
    ) -> pymongo.results.BulkWriteResult:
        """
        Reorders many resources in the custom order sent as body.
        `resources`: resources to be reordered
        `creator`: Creator object

        Type of body to send as `resources`:
        ```
        [{
            "resource_id": "resource.$id",
            "resource_ref": "resource.$ref",
            "position": 0,
        }]
        ```
        """
        result = self.sortings.bulk_write(
            [
                pymongo.UpdateOne(
                    filter={
                        "resource_ref.$ref": resource.resource_ref,
                        "resource_ref.$id": resource.resource_id,
                        "created_by.user_email": creator.user_email,
                    },
                    update={
                        "$set": {
                            "position": resource.position,
                            "updated_at": datetime.now(),
                        },
                        "$setOnInsert": {
                            "created_at": datetime.now(),
                            "created_by": creator.model_dump(by_alias=True),
                        },
                    },
                    upsert=True,
                )
                for resource in resources
            ]
        )
        return result

    def read_many(self, creator: Creator) -> list[CustomSorting]:
        """
        Returns the objects in the order they were sorted.
        `creator`: Creator object
        """

        # TODO: change this Any to specific type
        custom_sortings: pymongo.cursor.Cursor[Any] = self.sortings.find(
            filter={
                "resource_ref.$ref": self.collection,
                "created_by.user_email": creator.user_email,
            }
        ).sort("position", pymongo.ASCENDING)

        return list(custom_sortings)

    def read_many_whole_object(
        self, creator: Creator
    ) -> list[CustomSortingWithResource[T]]:
        """
        Returns the objects in the order they were sorted.
        `creator`: Creator object
        """
        # TODO: change this Any to specific type
        custom_sortings: pymongo.command_cursor.CommandCursor[Any] = (
            self.sortings.aggregate(
                # [
                #     {
                #         "$match": {
                #             "resource_ref.$ref": self.collection,
                #             "created_by.user_email": creator.user_email,
                #         }
                #     },
                #     # {
                #     #     "$lookup": {
                #     #         "from": self.collection,
                #     #         "localField": "resource_ref.$id",
                #     #         "foreignField": "_id",
                #     #         "as": "resource",
                #     #     }
                #     # },
                #     {"$sort": {"position": pymongo.ASCENDING}},
                # ]
                [
                    {
                        "$addFields": {
                            "resource_ref": {
                                "$arrayElemAt": [
                                    {"$objectToArray": "resource_ref"},
                                    1,
                                ]  # expected document, not string
                            }
                        }
                    },
                    {"$addFields": {"resource_ref": "resource_ref.v"}},
                    {
                        "$lookup": {
                            "from": self.collection,
                            "localField": "resource_ref",
                            "foreignField": "_id",
                            "as": "resource",
                        }
                    },
                    {
                        "$addFields": {
                            "resource_ref": {"$arrayElemAt": ["$resource_ref", 0]}
                        }
                    },
                ]
            )
        )
        return list(custom_sortings)

    def delete_one(
        self, position: int, creator: Creator, background_task: BackgroundTasks | None
    ) -> pymongo.results.DeleteResult:
        """
        Deletes a resource from the custom order according to the position.

        `position`: int position to be deleted
        `creator`: Creator object
        `background_task`: BackgroundTasks object (comes from route dependency), send None to not update the other objects positions after deletion
        """
        user_email = creator.user_email

        filter = {"position": position, "created_by.user_email": user_email}
        result: pymongo.results.DeleteResult = self.sortings.delete_one(filter)

        if result.deleted_count == 0:
            raise CustomOrderNotFound

        if background_task is not None:
            background_task.add_task(
                self.sortings.update_many,
                filter={
                    "position": {"$gt": position},
                    "resource_ref": {"$ref"},
                    "created_by.user_email": user_email,
                },
                update={"$inc": {"position": -1}},
            )
        return result

    def create_search_indexes(self) -> None:
        """
        Creates the indexes needed for the custom sortings.
        """
        logger.debug("Creating indexes for custom sortings")
        self.sortings.create_index([("resource.$ref", pymongo.ASCENDING)])
        self.sortings.create_index([("position", pymongo.ASCENDING)])
