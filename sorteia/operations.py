from datetime import datetime
import os
from annotated_types import T
from bson import ObjectId
from fastapi import BackgroundTasks
import pymongo
import dotenv

from redbaby.database import DB
from tauth.schemas import Creator

from .schemas import CustomSorting, CustomSortingWithResource
from .exceptions import CustomOrderNotSaved
from .models import CustomSortingDAO

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
        self.collection = collection_name
        self.sortings = DB.get()["custom-sortings"]

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
        resources: list,
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

        custom_sortings = self.sortings.find(
            filter={
                "resource_ref.$ref": self.collection,
            }
        ).sort("position", pymongo.ASCENDING)

        return [CustomSorting(**custom_sorting) for custom_sorting in custom_sortings]

    def read_many_whole_object(self) -> list[CustomSortingWithResource[T]]:
        """
        Returns the objects in the order they were sorted.
        """

        custom_sortings = self.sortings.aggregate(
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
    ):
        """
        position: int position to be deleted
        background_task: BackgroundTasks object (comes from route dependency)
        """
        user_email = creator.user_email

        filter = {"position": position}
        result = self.sortings.delete_one(filter)

        if result.deleted_count == 0:
            raise

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
        CustomSortingDAO.create_indexes()
