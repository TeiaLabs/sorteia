from datetime import datetime
import os
from bson import ObjectId
import pymongo
import dotenv

from redbaby.database import DB
from tauth.schemas import Creator

from .schemas import CustomSorting, CustomSortingWithResource
from .exceptions import CustomOrderNotSaved

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

    # copilot suggested it, maybe change it later
    def __init__(self, collection_name: str):
        """
        collection_name: collection name of the elements to be sorted
        """
        self.collection = collection_name
        self.sortings = DB.get()["custom-sortings"]


    def reorder_one(self, creator: Creator, resource_id: ObjectId, position: int ): 
        """
        creator: Creator object
        resource_id: ObjectId of the resource to be ordered
        position: int position to be set
        """

        filter = {"resource_ref": {"$ref": self.collection, "$id": resource_id}}

        custom_sorting = {
            "position": position,
            "resource_ref": {"$ref": self.collection, "$id": resource_id},
            "updated_at": datetime.now(),
        }
        update = {"$set": custom_sorting, "$setOnInsert": {'created_at': datetime.now(), "created_by": creator.model_dump(by_alias=True)}}

        result = self.sortings.update_one(filter=filter, update=update, upsert=True)
        if result.modified_count == 0 and result.upserted_id is None:
            raise CustomOrderNotSaved
        
        return result

    def join(self, resource_id: str) -> list:
        # sortings.filter(res.$ref, user).join(resource).sort(position)
        
        return []
    
