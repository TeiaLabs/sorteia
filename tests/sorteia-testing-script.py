import os
from bson import ObjectId
from dotenv import load_dotenv
from sorteia.operations import Sortings
from tauth.schemas import Creator
from pymongo import MongoClient
from sorteia.schemas import ReorderManyResourcesIn
from rich import print


class SortedThing:
    id: ObjectId
    name: str


load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client["athena"]
print("Connected to MongoDB")

# for i in range(1, 4):
# for i in range(1, 4):
#     db.other_things.insert_one({"name": f"thing{i}"})


items = db.sorted_things.find()
items_2 = db.other_things.find()
items = list(items)
items_2 = list(items_2)
# print(items)
client.close()

sortings = Sortings("sorted-things")

sortings_2 = Sortings("other-things")


creator = Creator(
    user_email="user@teialabs.com",
    token_name="token-test",
    client_name="client-test",
)

print(
    sortings_2.reorder_one(
        creator=creator,
        resource_id=items_2[0]["_id"],
        position=4,
    )
)

body_1 = ReorderManyResourcesIn(
    position=3,
    resource_id=items[1]["_id"],
    resource_ref="sorted-things",
)
body_2 = ReorderManyResourcesIn(
    position=2,
    resource_id=items[2]["_id"],
    resource_ref="sorted-things",
)

print(
    sortings.reorder_many(
        creator=Creator(
            user_email="user@teialabs.com",
            token_name="token-test",
            client_name="client-test",
        ),
        resources=[body_1, body_2],
    )
)

# print(sortings.read_many(creator=creator))

# print(sortings_2.read_many(creator=creator))
# db.sorted_things.find(filter={})

# print(sortings_2.read_many_whole_object(creator=creator))
sortings.delete_one(creator=creator, position=2, background_task=None)
