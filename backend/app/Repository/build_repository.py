from sqlalchemy import select

from app.Models.build import Build
from app.Repository.base_repository import BaseRepository


class BuildRepository(BaseRepository[Build]):
    model = Build

    def list_by_owner(self, user_id: int, skip: int, limit: int) -> tuple[list[Build], int]:
        stmt = select(Build).where(Build.user_id == user_id).order_by(Build.updated_at.desc(), Build.id.desc())
        return self.paginate(stmt, skip, limit)

    def list_public(self, skip: int, limit: int, search: str | None = None) -> tuple[list[Build], int]:
        stmt = select(Build).where(Build.is_public.is_(True)).order_by(Build.created_at.desc(), Build.id.desc())
        if search:
            stmt = stmt.where(Build.name.ilike(f"%{search}%"))
        return self.paginate(stmt, skip, limit)
