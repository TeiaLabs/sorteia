from annotated_types import T
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    HTTPException,
)
from loguru import logger
from redbaby.pyobjectid import PyObjectId
from tauth.schemas import Infostar

from sorteia import state_getter
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

    @router.get("/{resource}/", status_code=200, include_in_schema=False)
    @router.get("/{resource}", status_code=200)
    def get_sortings(
        resource: str,
        infostar: Infostar = Depends(state_getter.get("infostar")),
    ) -> list[CustomSortingWithResource[T]] | list[CustomSorting]:
        """Returns all custom order documents of a resource.

        - 200: OK
        - 400: Bad request
        - 401: Bad token
        - 403: Forbidden
        - 422: Unprocessable user input (bad body/query params)
        - 424: Problem with upstream server (e.g.: OpenAI)
        - 500: Internal server error
        """
        org = infostar.authprovider_org
        return Sortings(collection_name=resource, alias=org, db_name=org).read_many(
            infostar=infostar
        )

    @router.put("/{resource}/{position}", status_code=201)
    @router.put("/{resource}/{position}/", status_code=201, include_in_schema=False)
    def reorder_one(
        resource: str,
        position: int,
        background_task: BackgroundTasks,
        body: ReorderOneResourceIn = Body(..., openapi_examples=ReorderOneResourceIn.Config.examples),  # type: ignore
        infostar: Infostar = Depends(state_getter.get("infostar")),
    ) -> ReorderOneUpdatedOut | ReorderOneUpsertedOut:
        """Reorders a resource in the custom order.

        - 201: Created
        - 400: Bad request (e.g.: position out of bounds)
        - 401: Bad token
        - 403: Forbidden
        - 404: Object to be sorted not found
        - 500: Custom order not saved or Internal server error
        """
        org = infostar.authprovider_org
        try:
            sortings = Sortings(collection_name=resource, alias=org, db_name=org)
            return sortings.reorder_one(
                infostar=infostar,
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
                status_code=500,
                detail="Custom order not saved - maybe because of an internal error.",
            )
        except PositionOutOfBounds as e:
            logger.error("Position is out of bounds.")
            raise HTTPException(
                status_code=400,
                detail=f"{e.message} - {e.detail}",
            )

    @router.delete("/{resource}/{resource_id}", status_code=204)
    @router.delete(
        "/{resource}/{resource_id}/", status_code=204, include_in_schema=False
    )
    def delete_sorting(
        resource: str,
        resource_id: PyObjectId,
        background_task: BackgroundTasks,
        infostar: Infostar = Depends(state_getter.get("infostar")),
    ) -> None:
        """Deletes a resource from the custom order.

        - 204: No content
        - 400: Bad request
        - 401: Bad token
        - 403: Forbidden
        - 404: Custom order to be deleted not found
        - 422: Unprocessable user input (bad body/query params)
        - 424: Problem with upstream server (e.g.: OpenAI)
        - 500: Internal server error
        """
        org = infostar.authprovider_org
        try:
            Sortings(collection_name=resource, alias=org, db_name=org).delete_one(
                resource_id, infostar, background_task
            )
        except CustomOrderNotFound:
            logger.error("Custom sorting to be deleted was not found.")
            raise HTTPException(status_code=404, detail="Custom order not found.")

    @router.put("/{resource}", status_code=204)
    @router.put("/{resource}/", status_code=204)
    def reorder_many(
        resource: str,
        body: list[ReorderManyResourcesIn] = Body(..., openapi_examples=ReorderManyResourcesIn.Config.examples),  # type: ignore
        infostar: Infostar = Depends(state_getter.get("infostar")),
    ) -> None:
        """Reorders many resources in the custom order.

        - 204: No content
        - 400: Bad request (e.g.: position out of bounds)
        - 401: Bad token
        - 403: Forbidden
        - 500: Internal server error
        """
        org = infostar.authprovider_org
        try:
            Sortings(collection_name=resource, alias=org, db_name=org).reorder_many(
                resources=body, infostar=infostar
            )
        except PositionOutOfBounds as e:
            logger.error("Position is out of bounds.")
            raise HTTPException(
                status_code=400,
                detail=f"{e.message} - {e.detail}",
            )

    app.include_router(router)
