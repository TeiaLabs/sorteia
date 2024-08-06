from typing import Any

from pymongo.database import Database
from pytest import raises
from tauth.schemas import Infostar

from sorteia.exceptions import (
    CustomOrderNotFound,
    ObjectToBeSortedNotFound,
    PositionOutOfBounds,
)
from sorteia.operations import Sortings
from sorteia.schemas import (
    CustomSortingWithResource,
    ReorderManyResourcesIn,
    ReorderOneUpdatedOut,
    ReorderOneUpsertedOut,
)
from redbaby.pyobjectid import PyObjectId

from .conftest import Thing


def test_reorder_one_upsert(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.reorder_one(
        infostar=infostar_instances[0],
        resource_id=populate_db[0].id,
        position=2,
        background_task=None,
    )
    assert isinstance(result, ReorderOneUpsertedOut)
    assert result.id

    custom_order = mongo_connection["custom-sortings"].find_one(
        filter={"resource_id": populate_db[0].id, "position": 2}
    )
    assert custom_order


def test_reorder_one_update(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.reorder_one(
        infostar=infostar_instances[0],
        resource_id=populate_db[0].id,
        position=1,
        background_task=None,
    )
    assert isinstance(result, ReorderOneUpdatedOut)
    assert result.id

    custom_order = mongo_connection["custom-sortings"].find_one(
        filter={"resource_id": populate_db[0].id, "position": 1}
    )
    assert custom_order


def test_reorder_one_invalid_position(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    with raises(PositionOutOfBounds):
        sorting_instance.reorder_one(
            infostar=infostar_instances[0],
            resource_id=populate_db[0].id,
            position=100,
            background_task=None,
        )

    with raises(PositionOutOfBounds):
        sorting_instance.reorder_one(
            infostar=infostar_instances[0],
            resource_id=populate_db[0].id,
            position=-2,
            background_task=None,
        )


def test_reorder_many_invalid_positions(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    with raises(PositionOutOfBounds):
        sorting_instance.reorder_many(
            resources=[
                ReorderManyResourcesIn(
                    resource_id=populate_db[0].id,
                    resource_ref="things-test",
                    position=1,
                ),
                ReorderManyResourcesIn(
                    resource_id=populate_db[0].id,
                    resource_ref="things-test",
                    position=100,
                ),
            ],
            infostar=infostar_instances[0],
        )

    with raises(PositionOutOfBounds):
        sorting_instance.reorder_many(
            resources=[
                ReorderManyResourcesIn(
                    resource_id=populate_db[0].id,
                    resource_ref="things-test",
                    position=1,
                ),
                ReorderManyResourcesIn(
                    resource_id=populate_db[0].id,
                    resource_ref="things-test",
                    position=-1,
                ),
            ],
            infostar=infostar_instances[0],
        )


def test_reorder_many(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    body = [
        ReorderManyResourcesIn(
            resource_id=populate_db[1].id, resource_ref="things-test", position=0
        ),
        ReorderManyResourcesIn(
            resource_id=populate_db[3].id, resource_ref="things-test", position=2
        ),
    ]
    result = sorting_instance.reorder_many(
        resources=body, infostar=infostar_instances[0]
    )
    assert result

    first = mongo_connection["custom-sortings"].find_one(
        filter={
            "resource_collection": "things-test",
            "resource_id": populate_db[1].id,
            "position": 0,
        }
    )
    assert first
    third = mongo_connection["custom-sortings"].find_one(
        filter={
            "resource_collection": "things-test",
            "resource_id": populate_db[3].id,
            "position": 2,
        }
    )
    assert third


def test_reorder_one_with_invalid_id(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    with raises(ObjectToBeSortedNotFound):
        sorting_instance.reorder_one(
            infostar=infostar_instances[0],
            resource_id=PyObjectId(),
            position=2,
            background_task=None,
        )


def test_read_many_ordered(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.read_many(infostar=infostar_instances[0])
    assert len(result) == 3

    # populate_db[1]
    # populate_db[0]
    # populate_db[3]
    assert result[0]["resource_id"] == populate_db[1].id  # type: ignore
    assert result[1]["resource_id"] == populate_db[0].id  # type: ignore
    assert result[2]["resource_id"] == populate_db[3].id  # type: ignore


def test_read_many_not_creator(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.read_many(infostar=infostar_instances[1])
    assert len(result) == 1
    assert result[0]["resource_id"] == populate_db[-1].id  # type: ignore


def test_read_many_wholeobject(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result: list[CustomSortingWithResource[Any]] = (
        sorting_instance.read_many_whole_object(infostar=infostar_instances[0])
    )
    assert len(result) == 3

    assert result[0]["resource"]["name"] == populate_db[1].name  # type: ignore
    assert result[1]["resource"]["name"] == populate_db[0].name  # type: ignore
    assert result[2]["resource"]["name"] == populate_db[3].name  # type: ignore


def test_delete_custom_order(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.delete_one(
        resource_id=populate_db[1].id,
        infostar=infostar_instances[0],
        background_task=None,
    )

    assert result

    custom_order = mongo_connection["custom-sortings"].find_one(
        filter={"resource_id": populate_db[1].id, "position": 1}
    )
    assert custom_order is None

    rest = sorting_instance.read_many(infostar=infostar_instances[0])
    assert len(rest) == 2


def test_delete_nonexistant_custom_order(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    with raises(CustomOrderNotFound):
        sorting_instance.delete_one(
            resource_id=PyObjectId(),
            infostar=infostar_instances[0],
            background_task=None,
        )


def test_delete_one_with_background_task(
    sorting_instance: Sortings,
    infostar_instances: list[Infostar],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):  # still need to figure out how to mock the background task
    pass
