from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.session import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Operaciones comunes de acceso a datos; cada repositorio indica su `model`."""

    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, obj_id: int) -> ModelT | None:
        return self.db.get(self.model, obj_id)

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def save(self, obj: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.commit()

    def count(self, *criteria) -> int:
        stmt = select(func.count()).select_from(self.model)
        if criteria:
            stmt = stmt.where(*criteria)
        return self.db.scalar(stmt) or 0

    def paginate(self, stmt: Select, skip: int, limit: int) -> tuple[list[ModelT], int]:
        total = self.db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
        items = self.db.scalars(stmt.offset(skip).limit(limit)).unique().all()
        return list(items), total
