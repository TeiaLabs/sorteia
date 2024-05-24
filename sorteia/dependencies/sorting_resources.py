from typing import Literal

from annotated_types import T
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
)
from loguru import logger
from tauth.injections import privileges  # type: ignore
from tauth.schemas import Creator  # type: ignore

from sorteia.exceptions import (
    CustomOrderNotFound,
    CustomOrderNotSaved,
    ObjectToBeSortedNotFound,
    PositionOutOfBounds,
)
from sorteia.models import CustomSorting

from ..operations import Sortings
from ..schemas import (
    CustomSortingWithResource,
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
    ) -> list[CustomSortingWithResource[T] | CustomSorting]:  # type: ignore
        """Returns the custom order of a resource.

        Args:
            resource (str): resource name.
            sort (Literal["position"], optional): sort by position. Defaults to Query(default="position", alias="sort").
            resolve_refs (Literal["$resource_ref", "no"], optional): resolve references. Defaults to Header(default="no", alias="X-Resolve-Refs").
            creator (Creator): Creator object

        Returns:
            a list of CustomSortingWithResource or CustomSorting objects. Depending on the `X-Resolve-Refs` header.
            If header `X-Resolve-Refs` is set to `$resource_ref`, it will return the custom order with the whole object.
            If `no`, it will return only the custom order without the whole object.
        """
        org = creator.user_email.split("@")[1].split(".")[0]
        if resolve_refs == "$resource_ref":
            return Sortings(collection_name=resource, alias=org, db_name=org).read_many_whole_object(creator=creator)  # type: ignore
        return Sortings(collection_name=resource, alias=org, db_name=org).read_many(creator=creator)  # type: ignore

    @router.put("/{resource}/{position}", status_code=201)
    def reorder_one(  # type: ignore
        resource: str,
        position: int,
        background_task: BackgroundTasks,
        body: ReorderOneResourceIn = Body(..., openapi_examples=ReorderOneResourceIn.Config.examples),  # type: ignore
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> ReorderOneUpdatedOut | ReorderOneUpsertedOut:
        """Reorders a resource in the custom order.

        Args:
            resource(str): resource name.
            position(int): position to be inserted.
            body(ReorderOneResourceIn): ReorderOneResourceIn resource_id to be inserted.
            creator(Creator): Creator object.

        Returns:
            ReorderOneUpdatedOut or ReorderOneUpsertedOut object.

        Raises:
            HTTPException: (404) Object to be sorted not found.
            HTTPException: (400) Custom order not saved - maybe because of an internal error.
            HTTPException: (400) Position is out of bounds.
        """
        org = creator.user_email.split("@")[1].split(".")[0]
        try:
            return Sortings(
                collection_name=resource, alias=org, db_name=org
            ).reorder_one(
                creator=creator,
                resource_id=body.resource_id,
                position=position,
                background_task=background_task,
            )
        except ObjectToBeSortedNotFound:
            logger.error(
                "Object the user is trying to reorder was not found on the same database the order is going to be saved."
            )
            raise HTTPException(
                status_code=404,
                detail="Object to be sorted not found",
            )
        except CustomOrderNotSaved:
            logger.error("Custom order could not be saved.")
            raise HTTPException(
                status_code=400,
                detail="Custom order not saved - maybe because of an internal error.",
            )
        except PositionOutOfBounds as e:
            logger.error("Position is out of bounds.")
            raise HTTPException(
                status_code=400,
                detail=f"{e.message} - {e.detail}",
            )

    @router.delete("/{resource}/{position}", status_code=204)
    def delete_sorting(  # type: ignore
        resource: str,
        position: int,
        background_task: BackgroundTasks,
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> None:
        """Deletes a resource from the custom order.

        Args:
            resource(str): resource name.
            position(int): position to be deleted.
            creator(Creator): Creator object.

        Returns:
            None

        Raises:
            HTTPException: (404) Custom order not found.
        """
        org = creator.user_email.split("@")[1].split(".")[0]
        try:
            Sortings(collection_name=resource, alias=org, db_name=org).delete_one(
                position, creator, background_task
            )
        except CustomOrderNotFound:
            logger.error("Custom sorting to be deleted was not found.")
            raise HTTPException(status_code=404, detail="Custom order not found.")

    @router.put("/{resource}", status_code=204)
    def reorder_many(  # type: ignore
        resource: str,
        body: list[ReorderManyResourcesIn] = Body(..., openapi_examples=ReorderManyResourcesIn.Config.examples),  # type: ignore
        creator: Creator = Depends(privileges.is_valid_user),
    ) -> None:
        """Reorders many resources in the custom order.

        Args:
            resource(str): resource name.
            body(list[ReorderManyResourcesIn]): resources to be reordered.

        Returns:
            None

        Raises:
            HTTPException: (400) Position is out of bounds.
        """
        org = creator.user_email.split("@")[1].split(".")[0]
        try:
            Sortings(collection_name=resource, alias=org, db_name=org).reorder_many(
                resources=body, creator=creator
            )
        except PositionOutOfBounds as e:
            logger.error("Position is out of bounds.")
            raise HTTPException(
                status_code=400,
                detail=f"{e.message} - {e.detail}",
            )

    app.include_router(router)
