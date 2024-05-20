from typing import Any

from pymongo.cursor import Cursor
from pymongo.database import Database
from tauth.schemas import Creator  # type: ignore

from sorteia.operations import Sortings
from sorteia.schemas import (
    ReorderManyResourcesIn,
    ReorderOneUpdatedOut,
    ReorderOneUpsertedOut,
)

from .conftest import Thing


def test_reorder_one_upsert(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.reorder_one(
        creator=creators_instances[0], resource_id=populate_db[0].id, position=3
    )
    assert isinstance(result, ReorderOneUpsertedOut)
    assert result.id

    custom_order: Cursor[Any] = mongo_connection["custom-sortings"].find(
        filter={"resource_ref.$id": populate_db[0].id, "position": 3}
    )
    assert len(list(custom_order)) == 1


def test_reorder_one_update(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.reorder_one(
        creator=creators_instances[0],
        resource_id=populate_db[0].id,
        position=2,
    )
    assert isinstance(result, ReorderOneUpdatedOut)
    assert result.id

    custom_order: Cursor[Any] = mongo_connection["custom-sortings"].find(
        filter={"resource_ref.$id": populate_db[0].id, "position": 2}
    )
    assert len(list(custom_order)) == 1


def test_reorder_many(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    body = [
        ReorderManyResourcesIn(
            resource_id=populate_db[1].id, resource_ref="things-test", position=1
        ),
        ReorderManyResourcesIn(
            resource_id=populate_db[3].id, resource_ref="things-test", position=3
        ),
    ]
    result = sorting_instance.reorder_many(
        resources=body, creator=creators_instances[0]
    )
    assert result

    # dbref not working on queries ($id)
    # first: Cursor[Any] = mongo_connection["custom-sortings"].find(
    #     filter={
    #         "$and": [
    #             {"resource_ref": DBRef("custom-sortings", populate_db[1].id)},
    #             {"position": 1},
    #         ]
    #     }
    # )
    # assert len(list(first)) == 1
    # third: Cursor[Any] = mongo_connection["custom-sortings"].find(
    #     filter={
    #         "$and": [
    #             {"resource_ref": DBRef("custom-sortings", populate_db[3].id)},
    #             {"position": 1},
    #         ]
    #     }
    # )
    # third_listed = list(third)
    # logger.debug(f"ID 3: {populate_db[3].id}")
    # logger.debug(third_listed)
    # assert len(third_listed) == 1


def test_reorder_many_with_invalid_ids(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    pass


def test_reorder_one_with_invalid_id(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    pass


def test_read_many_ordered(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.read_many(creator=creators_instances[0])
    assert len(result) == 3

    # populate_db[1]
    # populate_db[0]
    # populate_db[3]
    assert result[0]["resource_ref"].id == populate_db[1].id  # type: ignore
    assert result[0]["resource_ref"].id == populate_db[1].id  # type: ignore
    assert result[1]["resource_ref"].id == populate_db[0].id  # type: ignore
    assert result[2]["resource_ref"].id == populate_db[3].id  # type: ignore


def test_read_many_not_creator(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    result = sorting_instance.read_many(creator=creators_instances[1])
    assert len(result) == 1
    assert result[0]["resource_ref"].id == populate_db[-1].id  # type: ignore


def test_read_many_wholeobject(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    pass


def test_delete_custom_order(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):
    pass


def test_delete_nonexistant_custom_order(
    sorting_instance: Sortings,
    creators_instances: list[Creator],
    populate_db: list[Thing],
    mongo_connection: Database[Any],
):  # invalid position
    pass
