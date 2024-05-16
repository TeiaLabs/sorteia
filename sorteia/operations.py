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
from redbaby.database import DB  # type: ignore
from tauth.schemas import Creator  # type: ignore

from .exceptions import CustomOrderNotFound, CustomOrderNotSaved
from .models import CustomSorting, CustomSortingWithResource
from .schemas import ReorderManyResourcesIn, ReorderOneUpdatedOut, ReorderOneUpsertedOut
from .utils import PyObjectId  # type: ignore

load_dotenv()

# TODO: add on env and settings
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# db connection to add custom sortings
DB.add_conn(
    db_name=DB_NAME,
    uri=MONGO_URI,
    alias="default",
    start_client=True,
)


class Sortings:

    def __init__(self, collection_name: str):
        """
        collection_name: collection name of the elements to be sorted
        """
        print("Creating the sortings thingy")
        self.collection: str = collection_name
        self.sortings = DB.get()["custom-sortings"]  # type: ignore
        self.create_search_indexes()
        print("Created the sortings thingy")

    def reorder_one(
        self, creator: Creator, resource_id: PyObjectId, position: int
    ) -> ReorderOneUpsertedOut | ReorderOneUpdatedOut:
        """
        Reorders a resource in the custom order.
        creator: Creator object
        resource_id: ObjectId of the resource to be ordered
        position: int position to be set
        """

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

        result = self.sortings.update_one(filter=filter, update=update, upsert=True)

        if result.upserted_id is not None:
            return ReorderOneUpsertedOut(
                id=result.upserted_id,
                created_at=created_at,
                updated_at=updated_at,
                created_by=creator,
            )
        elif result.modified_count == 1:
            from rich import print

            print(result.raw_result)
            return ReorderOneUpdatedOut(
                id=PyObjectId("hi"),
                updated_at=updated_at,
            )
        else:
            raise CustomOrderNotSaved

    def reorder_many(
        self,
        resources: list[ReorderManyResourcesIn],
        creator: Creator,
    ) -> pymongo.results.BulkWriteResult:
        result = self.sortings.bulk_write(
            [
                pymongo.UpdateOne(
                    filter={
                        "resource_ref.$ref": self.collection,
                        "resource_ref.$id": resource._id,
                        "created_by.user_email": creator.user_email,
                    },
                    update={
                        "$set": {
                            "position": i,
                            "updated_at": datetime.now(),
                        },
                        "$setOnInsert": {
                            "created_at": datetime.now(),
                            "created_by": creator.model_dump(by_alias=True),
                        },
                    },
                    upsert=True,
                )
                for i, resource in enumerate(resources)
            ]
        )
        return result

    def read_many(self) -> list[CustomSorting]:
        """
        Returns the objects in the order they were sorted.
        """

        # TODO: change this Any to specific type
        custom_sortings: pymongo.cursor.Cursor[Any] = self.sortings.find(
            filter={
                "resource_ref.$ref": self.collection,
            }
        ).sort("position", pymongo.ASCENDING)

        return [CustomSorting(**custom_sorting) for custom_sorting in custom_sortings]

    def read_many_whole_object(
        self,
    ) -> list[CustomSortingWithResource[T]]:
        """
        Returns the objects in the order they were sorted.
        """

        # TODO: change this Any to specific type
        custom_sortings: pymongo.command_cursor.CommandCursor[Any] = (
            self.sortings.aggregate(
                [
                    {
                        "$match": {
                            "resource_ref.$ref": self.collection,
                        }
                    },
                    {
                        "$lookup": {
                            "from": self.collection,
                            "localField": "resource_ref.$id",
                            "foreignField": "_id",
                            "as": "resource",
                        }
                    },
                    {"$sort": {"position": pymongo.ASCENDING}},
                ]
            )
        )

        return [
            CustomSortingWithResource(**custom_sorting)
            for custom_sorting in custom_sortings
        ]

    def delete_one(
        self, position: int, creator: Creator, background_task: BackgroundTasks
    ) -> pymongo.results.DeleteResult:
        """
        position: int position to be deleted
        background_task: BackgroundTasks object (comes from route dependency)
        """
        # user_email = creator.user_email

        filter = {"position": position}
        result: pymongo.results.DeleteResult = self.sortings.delete_one(filter)

        if result.deleted_count == 0:
            raise CustomOrderNotFound

        background_task.add_task(
            self.sortings.update_many,
            filter={"position": {"$gt": position}, "resource_ref": {"$ref"}},
            update={"$inc": {"position": -1}},
        )
        return result

    def create_search_indexes(self) -> None:
        """
        Creates the indexes needed for the custom sortings.
        """
        self.sortings.create_index([("resource.$ref", pymongo.ASCENDING)])
        self.sortings.create_index([("position", pymongo.ASCENDING)])
