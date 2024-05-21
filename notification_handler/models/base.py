import typing
import uuid
from typing import TypeVar

import orjson
import pydantic


def orjson_dumps(
        v: typing.Any,
        *,
        default: typing.Callable[[typing.Any], typing.Any] | None,
) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(json_encoders={uuid.UUID: lambda x: f"{x}"})


T = TypeVar("T", bound=BaseModel)


# Utility function to convert SQLAlchemy objects to Pydantic models.
def to_pydantic(db_object: BaseModel, pydantic_model: type[T]) -> T:
    return pydantic_model(**db_object.__dict__)
