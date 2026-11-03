from __future__ import annotations

from sqlalchemy import exists, func, select

from app.Models.advisory import AdvisoryRequest, AdvisoryStatus
from app.Repository.base_repository import BaseRepository


class AdvisoryRepository(BaseRepository[AdvisoryRequest]):
    model = AdvisoryRequest

    def list(
        self,
        skip: int,
        limit: int,
        user_id: int | None = None,
        advisor_id: int | None = None,
        status: AdvisoryStatus | None = None,
        unassigned: bool = False,
    ) -> tuple[list[AdvisoryRequest], int]:
        stmt = select(AdvisoryRequest).order_by(AdvisoryRequest.created_at.desc(), AdvisoryRequest.id.desc())
        if user_id is not None:
            stmt = stmt.where(AdvisoryRequest.user_id == user_id)
        if advisor_id is not None:
            stmt = stmt.where(AdvisoryRequest.advisor_id == advisor_id)
        if unassigned:
            stmt = stmt.where(AdvisoryRequest.advisor_id.is_(None))
        if status is not None:
            stmt = stmt.where(AdvisoryRequest.status == status)
        return self.paginate(stmt, skip, limit)

    def is_build_recommended_to(self, build_id: int, user_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(
            AdvisoryRequest.recommended_build_id == build_id, AdvisoryRequest.user_id == user_id
        ))))

    def count_by_status(self) -> dict[str, int]:
        rows = self.db.execute(
            select(AdvisoryRequest.status, func.count()).group_by(AdvisoryRequest.status)
        ).all()
        counts = {status.value: 0 for status in AdvisoryStatus}
        counts.update({status.value: total for status, total in rows})
        return counts
