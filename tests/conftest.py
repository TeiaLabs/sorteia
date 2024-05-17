import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.database import Database
from tauth.schemas import Creator  # type: ignore

from sorteia.operations import Sortings
from sorteia.utils import PyObjectId


class Thing(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str


load_dotenv()


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def mongo_connection() -> Database[Any]:
    client: MongoClient[Any] = MongoClient(os.getenv("MONGO_URI"))
    db: Database[Any] = client["sorteia-test"]
    return db


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def sorting_instance() -> Sortings:
    return Sortings("things-test")


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def creators_instances() -> list[Creator]:
    return [
        Creator(
            user_email="user@teialabs.com", client_name="client", token_name="token"
        ),
        Creator(
            user_email="user2@teialabs.com", client_name="client", token_name="token"
        ),
    ]


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def create_index(sorting_instance: Sortings):
    sorting_instance.create_search_indexes()


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def populate_db(mongo_connection: Database[Any]) -> list[Thing]:
    db = mongo_connection
    objects = [{"_id": PyObjectId(), "name": f"thing{i}"} for i in range(1, 4)]

    db["things-test"].insert_many(objects)

    return [Thing(**obj) for obj in objects]  # type: ignore


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def teardown_db(mongo_connection: Database[Any]):
    yield
    mongo_connection.drop_collection("things-test")
