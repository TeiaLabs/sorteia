from fastapi import APIRouter, BackgroundTasks, FastAPI
from tauth.schemas import Creator

from ..operations import Sortings


def add_sorting_resources_dependency(app: FastAPI) -> None:
    router = APIRouter(prefix="/sortings", tags=["sortings"])

    # - GET /sortings/{resource}?sort=position

    # - GET /sortings/{resource}?sort=position
    # - Header X-Resolve-Refs: $resource_ref

    # - PUT /sortings/{resource}/:position

    @router.delete("/{resource}/{position}", status_code=204)
    def delete_sorting(
        resource: str,
        position: int,
        creator: Creator,
        background_task: BackgroundTasks,
    ) -> None:
        """
        position: int position to be deleted
        """
        result = Sortings(resource).delete_one(position, creator, background_task)

        if result.deleted_count == 0:
            # raise custom error
            raise


    #- PUT /sortings/{resource}
