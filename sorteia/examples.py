from melting_schemas.utils import wrap, to_openapi_examples
from fastapi.openapi.models import Example

from .schemas import ReorderManyResourcesIn, ReorderManyResourcesInList, ReorderOneResourceIn
from redbaby.pyobjectid import PyObjectId


def reorder_many_examples() -> dict[str, Example]:
    reorder_many = ReorderManyResourcesInList(
        resources=[
            ReorderManyResourcesIn(
                resource_id=PyObjectId(),
                resource_ref="resource.$ref",
                position=0,
            ),
            ReorderManyResourcesIn(
                resource_id=PyObjectId(),
                resource_ref="resource.$ref",
                position=1,
            ),
        ]
    )
    return to_openapi_examples(
        [wrap(name="Reorder Many Resources", value=reorder_many)]
    )


def reorder_one_examples() -> dict[str, Example]:
    reorder_one = ReorderOneResourceIn(
        resource_id=PyObjectId(),
    )
    return to_openapi_examples([wrap(name="Reorder One Resource", value=reorder_one)])
