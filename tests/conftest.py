import os
from typing import Any

import pytest
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.database import Database
from redbaby.pyobjectid import PyObjectId
from tauth.schemas.infostar import Infostar, InfostarExtra

from sorteia.operations import Sortings


class Thing(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    created_by: Infostar


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
def infostar_instances() -> list[Infostar]:
    return [
        Infostar(
            request_id=PyObjectId(),
            apikey_name="teialabs",
            authprovider_type="auth0",
            authprovider_org="teialabs",
            extra=InfostarExtra(
                geolocation="",
                jwt_sub="",
                os="",
                url="",
                user_agent="",
            ),
            service_handle="allai--code",
            user_handle="teialabs@teialabs.com",
            user_owner_handle="teialabs",
            client_ip="",
        ),
        Infostar(
            request_id=PyObjectId(),
            apikey_name="teialabs",
            authprovider_type="auth0",
            authprovider_org="teialabs",
            extra=InfostarExtra(
                geolocation="",
                jwt_sub="",
                os="",
                url="",
                user_agent="",
            ),
            service_handle="allai--code",
            user_handle="teialabs-instance2@teialabs.com",
            user_owner_handle="teialabs",
            client_ip="",
        ),
    ]


@pytest.fixture(scope="session", autouse=True)
def populate_db(
    mongo_connection: Database[Any],
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
) -> list[Thing]:
    db = mongo_connection
    objects = [
        {
            "_id": PyObjectId(),
            "name": f"thing{i}",
            "created_by": infostar_instances[0].model_dump(by_alias=True),
        }
        for i in range(1, 4)
    ]
    for i in range(3):
        objects.append(
            {
                "_id": PyObjectId(),
                "name": f"thing{i}",
                "created_by": infostar_instances[1].model_dump(by_alias=True),
            }
        )

    db["things-test"].insert_many(objects)
    sorting_instance.reorder_one(
        infostar=infostar_instances[1],
        resource_id=objects[-1]["_id"],
        position=2,
        background_task=None,
    )

    return [Thing(**obj) for obj in objects]  # type: ignore


@pytest.fixture(scope="session", autouse=True)
def teardown_db(mongo_connection: Database[Any]):
    yield
    mongo_connection.drop_collection("things-test")
    mongo_connection.drop_collection("custom-sortings")
