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

    @router.get("/{resource}", status_code=200)
    def get_sortings(  # type: ignore
        resource: str,
        sort: Literal["position"] = Query(default="position", alias="sort"),
        resolve_refs: Literal["$resource_ref", "no"] = Header(
            default="no", alias="X-Resolve-Refs"
        ),
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> list[CustomSorting | CustomSortingWithResource[T]]:  # type: ignore
        """
        Returns the custom order of a resource.

        If header `X-Resolve-Refs` is set to `$resource_ref`, it will return the custom order with the whole object. If `no`, it will return only the custom order without the whole object.
        `resource`: str resource name

        `resource`: str resource name
        `sort`: Literal["position"] sort by position
        `resolve_refs`: Literal["$resource_ref", "no"] resolve references
        `creator`: Creator object
        """
        if resolve_refs == "$resource_ref":
            return Sortings(resource).read_many_whole_object(creator=creator)  # type: ignore
        return Sortings(resource).read_many(creator=creator)  # type: ignore

    @router.put("/{resource}/{position}", status_code=201)
    def reorder_one(  # type: ignore
        resource: str,
        position: int,
        body: ReorderOneResourceIn = Body(..., openapi_examples=ReorderOneResourceIn.Config.examples),  # type: ignore
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> ReorderOneUpdatedOut | ReorderOneUpsertedOut:
        """
        Reorders a resource in the custom order.

        `resource`: str resource name
        `position`: int position to be inserted
        `body`: ReorderOneResourceIn resource_id to be inserted
        `creator`: Creator object

        Type of the ReorderOneResourceIn:
        ```
        {"resource_id": "pyobjectid"}
        ```
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
        Deletes a resource from the custom order.

        `resource`: str resource name
        `position`: int position to be deleted
        `creator`: Creator object
        """
        Sortings(resource).delete_one(position, creator, background_task)

    @router.put("/{resource}", status_code=204)
    def reorder_many(  # type: ignore
        resource: str,
        body: list[ReorderManyResourcesIn] = Body(..., openapi_examples=ReorderManyResourcesIn.Config.examples),  # type: ignore
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> None:
        """
        `resource`: str resource name
        `body`: list[ReorderManyResourcesIn] resources to be reordered

        Type of the ReorderManyResourcesIn:
        ```
        [{
            "resource_id": "resource.$id",
            "resource_ref": "resource.$ref",
            "position": 0,
        }]
        ```
        """
        Sortings(resource).reorder_many(resources=body, creator=creator)

    app.include_router(router)
