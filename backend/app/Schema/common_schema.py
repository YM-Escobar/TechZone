from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, PlainSerializer

T = TypeVar("T")

# Los montos se validan como Decimal, pero se envían al frontend como número
Money = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


@dataclass
class PageResult(Generic[T]):
    """Lo que devuelven los services al paginar; FastAPI lo valida contra Page[...]."""

    items: list[T]
    total: int
    skip: int
    limit: int


class Message(BaseModel):
    detail: str


def update_data(schema: BaseModel, nullable: frozenset[str] | set[str] = frozenset()) -> dict[str, Any]:
    """Campos enviados en un PATCH; ignora null en los campos que no se pueden vaciar."""
    return {
        field: value
        for field, value in schema.model_dump(exclude_unset=True).items()
        if value is not None or field in nullable
    }
