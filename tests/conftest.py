import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pymongo import MongoClient

from sorteia.utils import PyObjectId
from sorteia.operations import Sortings
from loguru import logger


class Thing(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str


load_dotenv()


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def sorting_instance() -> Sortings:
    return Sortings("things-test")


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def create_index(sorting_instance: Sortings):
    sorting_instance.create_search_indexes()


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def populate_db() -> list[Thing]:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["sorteia-test"]
    logger.debug("Connected to MongoClient")

    objects = [{"_id": PyObjectId(), "name": f"thing{i}"} for i in range(1, 4)]

    db["things-test"].insert_many(objects)

    return [Thing(**obj) for obj in objects]


@pytest.fixture(scope="session", autouse=True)  # type: ignore
def teardown_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["sorteia-test"]
    logger.debug("Connected to MongoClient")
    yield
    db.drop_collection("things-test")
