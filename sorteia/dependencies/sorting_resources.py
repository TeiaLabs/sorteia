from typing import Literal

from annotated_types import T
from fastapi import APIRouter, BackgroundTasks, Body, Depends, FastAPI, Header, Query
from tauth.injections import privileges  # type: ignore
from tauth.schemas import Creator  # type: ignore

from sorteia.models import CustomSorting, CustomSortingWithResource

from ..operations import Sortings
from ..schemas import (
    ReorderManyResourcesIn,
    ReorderOneResourceIn,
    ReorderOneUpdatedOut,
    ReorderOneUpsertedOut,
)


def add_sorting_resources_dependency(app: FastAPI) -> None:
    router = APIRouter(prefix="/sortings", tags=["sortings"])

    # TODO: fix the header literal types
    @router.get("/{resource}", status_code=200)
    def get_sortings(  # type: ignore
        resource: str,
        sort: Literal["position"] = Query(default="position", alias="sort"),
        resolve_refs: Literal["$resource", "no"] = Header(
            default="no", alias="X-Resolve-Refs"
        ),
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> list[CustomSorting | CustomSortingWithResource[T]]:
        """
        resource: str resource name
        """
        if resolve_refs == "$resource":
            return Sortings(resource).read_many_whole_object()

        return Sortings(resource).read_many()

    @router.put("/{resource}/{position}", status_code=201)
    def reorder_one(  # type: ignore
        resource: str,
        position: int,
        body: ReorderOneResourceIn = Body(..., openapi_examples=ReorderOneResourceIn.Config.examples),  # type: ignore
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> ReorderOneUpdatedOut | ReorderOneUpsertedOut:
        """
        position: int position to be inserted
        """
        return Sortings(resource).reorder_one(
            creator=creator, resource_id=body.resource_id, position=position
        )

    @router.delete("/{resource}/{position}", status_code=204)
    def delete_sorting(  # type: ignore
        resource: str,
        position: int,
        creator: Creator,
        background_task: BackgroundTasks,
    ) -> None:
        """
        position: int position to be deleted
        """
        Sortings(resource).delete_one(position, creator, background_task)

    @router.put("/{resource}", status_code=204)
    def reorder_many(  # type: ignore
        resource: str,
        body: list[ReorderManyResourcesIn] = Body(..., openapi_examples=ReorderManyResourcesIn.Config.examples),  # type: ignore
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> None:
        """
        resource: str resource name
        """
        Sortings(resource).reorder_many(resources=body, creator=creator)

    app.include_router(router)
