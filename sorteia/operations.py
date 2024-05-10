import os
import pymongo
import dotenv
from redbaby.database import DB

from .schemas import CustomSorting, CustomSortingWithResource

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
    def __init__(self):
        self.sortings = DB.get()["custom-sortings"]

    # upsert_one(filters,data)
    def reorder_one(self): 
        pass

    def join(self, resource : CustomSorting | CustomSortingWithResource) -> list:
        # sortings.filter(res.$ref, user).join(resource).sort(position)
        
        return []
    
