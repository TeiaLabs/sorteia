import os
from typing import Any

import pytest
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.database import Database
from tauth.schemas import Creator  # type: ignore

from sorteia.operations import Sortings
from sorteia.utils import PyObjectId

from loguru import logger


class Thing(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    created_by: dict[str, Any]


load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def mongo_connection() -> Database[Any]:
    logger.debug("Trying to connect to MongoDB")
    client: MongoClient[Any] = MongoClient(os.getenv("MONGO_URI"))
    db: Database[Any] = client["athena"]
    logger.debug("Connected to MongoDB")
    return db


@pytest.fixture(scope="session", autouse=True)
def sorting_instance() -> Sortings:
    return Sortings("things-test")


@pytest.fixture(scope="session", autouse=True)
def creators_instances() -> list[Creator]:
    return [
        Creator(
            user_email="user@teialabs.com", client_name="client", token_name="token"
        ),
        Creator(
            user_email="user2@teialabs.com", client_name="client", token_name="token"
        ),
    ]


@pytest.fixture(scope="session", autouse=True)
def populate_db(
    mongo_connection: Database[Any],
    sorting_instance: Sortings,
    creators_instances: list[Creator],
) -> list[Thing]:
    db = mongo_connection
    objects = [
        {
            "_id": PyObjectId(),
            "name": f"thing{i}",
            "created_by": creators_instances[0].model_dump(by_alias=True),
        }
        for i in range(1, 4)
    ]
    for i in range(3):
        objects.append(
            {
                "_id": PyObjectId(),
                "name": f"thing{i}",
                "created_by": creators_instances[1].model_dump(by_alias=True),
            }
        )

    db["things-test"].insert_many(objects)
    sorting_instance.reorder_one(
        creator=creators_instances[1],
        resource_id=objects[-1]["_id"],  # type: ignore
        position=2,
    )

    return [Thing(**obj) for obj in objects]  # type: ignore


@pytest.fixture(scope="session", autouse=True)
def teardown_db(mongo_connection: Database[Any]):
    yield
    mongo_connection.drop_collection("things-test")
    mongo_connection.drop_collection("custom-sortings")
