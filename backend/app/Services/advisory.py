from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.Models.advisory import AdvisoryRequest, AdvisoryStatus
from app.Models.user import User
from app.Repository.advisory_repository import AdvisoryRepository
from app.Repository.build_repository import BuildRepository
from app.Repository.user_repository import UserRepository
from app.Schema.advisory_schema import AdvisoryCreate, AdvisoryRespond, AdvisoryUpdate
from app.Schema.common_schema import PageResult, update_data
from app.Services import mailer

OPEN_STATUSES = (AdvisoryStatus.PENDING, AdvisoryStatus.IN_PROGRESS)


class AdvisoryService:
    def __init__(self, db: Session):
        self.advisories = AdvisoryRepository(db)
        self.builds = BuildRepository(db)
        self.users = UserRepository(db)

    # Usuario que solicita la asesoría

    def create(self, user: User, data: AdvisoryCreate) -> AdvisoryRequest:
        return self.advisories.add(AdvisoryRequest(user_id=user.id, **data.model_dump()))

    def list_mine(
        self, user: User, skip: int, limit: int, status: AdvisoryStatus | None = None
    ) -> PageResult[AdvisoryRequest]:
        items, total = self.advisories.list(skip, limit, user_id=user.id, status=status)
        return PageResult(items, total, skip, limit)

    def get(self, advisory_id: int, viewer: User) -> AdvisoryRequest:
        advisory = self.advisories.get(advisory_id)
        if advisory is None or (advisory.user_id != viewer.id and not viewer.is_staff):
            raise NotFoundError("Asesoría no encontrada")
        return advisory

    def update(self, advisory_id: int, user: User, data: AdvisoryUpdate) -> AdvisoryRequest:
        advisory = self._get_own(advisory_id, user)
        if advisory.status != AdvisoryStatus.PENDING:
            raise ConflictError("Solo puedes editar una asesoría mientras está pendiente")
        for field, value in update_data(data, {"preferences"}).items():
            setattr(advisory, field, value)
        return self.advisories.save(advisory)

    def cancel(self, advisory_id: int, user: User) -> AdvisoryRequest:
        advisory = self._get_own(advisory_id, user)
        if advisory.status not in OPEN_STATUSES:
            raise ConflictError("Esta asesoría ya fue cerrada")
        advisory.status = AdvisoryStatus.CANCELLED
        return self.advisories.save(advisory)

    # Asesores y administradores

    def list_all(
        self,
        skip: int,
        limit: int,
        status: AdvisoryStatus | None = None,
        advisor_id: int | None = None,
        unassigned: bool = False,
    ) -> PageResult[AdvisoryRequest]:
        items, total = self.advisories.list(
            skip, limit, status=status, advisor_id=advisor_id, unassigned=unassigned
        )
        return PageResult(items, total, skip, limit)

    def assign(self, advisory_id: int, actor: User, advisor_id: int | None = None) -> AdvisoryRequest:
        advisory = self.get(advisory_id, actor)
        if advisory.status not in OPEN_STATUSES:
            raise ConflictError("No se puede asignar una asesoría cerrada")

        if advisor_id is None or advisor_id == actor.id:
            advisor = actor
        elif actor.is_admin:
            advisor = self.users.get(advisor_id)
            if advisor is None or not advisor.is_active or not advisor.is_staff:
                raise BadRequestError("El usuario indicado no es un asesor activo")
        else:
            raise ForbiddenError("Solo un administrador puede asignar la asesoría a otra persona")

        if advisory.advisor_id not in (None, advisor.id) and not actor.is_admin:
            raise ConflictError("Esta asesoría ya la tiene asignada otro asesor")

        advisory.advisor_id = advisor.id
        advisory.status = AdvisoryStatus.IN_PROGRESS
        return self.advisories.save(advisory)

    def respond(
        self,
        advisory_id: int,
        actor: User,
        data: AdvisoryRespond,
        background_tasks: BackgroundTasks | None = None,
    ) -> AdvisoryRequest:
        advisory = self.get(advisory_id, actor)
        if advisory.status not in OPEN_STATUSES:
            raise ConflictError("Esta asesoría ya fue cerrada")
        if advisory.advisor_id not in (None, actor.id) and not actor.is_admin:
            raise ForbiddenError("Esta asesoría está asignada a otro asesor")

        if data.recommended_build_id is not None:
            build = self.builds.get(data.recommended_build_id)
            if build is None:
                raise BadRequestError("La build recomendada no existe")
            if build.user_id != actor.id and not actor.is_admin:
                raise ForbiddenError("Solo puedes recomendar builds creadas por ti")

        advisory.advisor_id = advisory.advisor_id or actor.id
        advisory.advisor_notes = data.advisor_notes
        advisory.recommended_build_id = data.recommended_build_id
        advisory.status = AdvisoryStatus.COMPLETED
        advisory.completed_at = datetime.now(timezone.utc)
        advisory = self.advisories.save(advisory)
        mailer.send_advisory_completed_email(background_tasks, advisory)
        return advisory

    # Solo administradores

    def change_status(self, advisory_id: int, actor: User, status: AdvisoryStatus) -> AdvisoryRequest:
        advisory = self.get(advisory_id, actor)
        advisory.status = status
        advisory.completed_at = datetime.now(timezone.utc) if status == AdvisoryStatus.COMPLETED else None
        if status == AdvisoryStatus.PENDING:
            advisory.advisor_id = None
        return self.advisories.save(advisory)

    def delete(self, advisory_id: int, actor: User) -> None:
        self.advisories.delete(self.get(advisory_id, actor))

    def _get_own(self, advisory_id: int, user: User) -> AdvisoryRequest:
        advisory = self.advisories.get(advisory_id)
        if advisory is None or advisory.user_id != user.id:
            raise NotFoundError("Asesoría no encontrada")
        return advisory
