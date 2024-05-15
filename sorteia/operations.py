import os
import pymongo

from typing import Any
from bson import ObjectId
from datetime import datetime
from annotated_types import T
from fastapi import BackgroundTasks
from dotenv import load_dotenv 

import pymongo.command_cursor
import pymongo.cursor
import pymongo.results
from redbaby.database import DB # type: ignore
from tauth.schemas import Creator # type: ignore

from .models import CustomSorting, CustomSortingWithResource
from .schemas import ReorderResourcesIn
from .exceptions import CustomOrderNotFound, CustomOrderNotSaved

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
        self.collection : str = collection_name
        self.sortings = DB.get()["custom-sortings"] # type: ignore
        self.create_search_indexes()
        print("Created the sortings thingy")

    def reorder_one(self, creator: Creator, resource_id: ObjectId, position: int):
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

        custom_sorting = {
            "position": position,
            "resource_ref": {"$ref": self.collection, "$id": resource_id},
            "updated_at": datetime.now(),
        }
        update = {
            "$set": custom_sorting,
            "$setOnInsert": {
                "created_at": datetime.now(),
                "created_by": creator.model_dump(by_alias=True),
            },
        }

        result = self.sortings.update_one(filter=filter, update=update, upsert=True)
        if result.modified_count == 0 and result.upserted_id is None:
            raise CustomOrderNotSaved

        return result

    def reorder_many(
        self,
        resources: list[ReorderResourcesIn],
        creator: Creator,
    ):
        self.sortings.bulk_write(
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

    def read_many(self) -> list[CustomSorting]:
        """
        Returns the objects in the order they were sorted.
        """

        # TODO: change this Any to specific type
        custom_sortings : pymongo.cursor.Cursor[Any] = self.sortings.find(
            filter={
                "resource_ref.$ref": self.collection,
            }
        ).sort("position", pymongo.ASCENDING)

        return [CustomSorting(**custom_sorting) for custom_sorting in custom_sortings]

    def read_many_whole_object(self) -> list[CustomSortingWithResource[T]]:
        """
        Returns the objects in the order they were sorted.
        """

        # TODO: change this Any to specific type
        custom_sortings : pymongo.command_cursor.CommandCursor[Any] = self.sortings.aggregate(
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
        result : pymongo.results.DeleteResult = self.sortings.delete_one(filter)

        if result.deleted_count == 0:
            raise CustomOrderNotFound

        background_task.add_task(
            self.sortings.update_many,
            filter={"position": {"$gt": position}, "resource_ref": {"$ref"}},
            update={"$inc": {"position": -1}},
        )
        return result

    def create_search_indexes(self):
        """
        Creates the indexes needed for the custom sortings.
        """
        self.sortings.create_index([("resource.$ref", pymongo.ASCENDING)])
        self.sortings.create_index([("position", pymongo.ASCENDING)])
      
