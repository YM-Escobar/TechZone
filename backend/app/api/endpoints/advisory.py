from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, status

from app.api.deps import AdminUser, CurrentUser, DbSession, PaginationDep, StaffUser, VerifiedUser
from app.Models.advisory import AdvisoryStatus
from app.Schema.advisory_schema import (
    AdvisoryAssign,
    AdvisoryCreate,
    AdvisoryOut,
    AdvisoryRespond,
    AdvisoryStatusUpdate,
    AdvisoryUpdate,
)
from app.Schema.common_schema import Page
from app.Services.advisory import AdvisoryService

router = APIRouter(prefix="/advisories", tags=["asesorías"])


def get_service(db: DbSession) -> AdvisoryService:
    return AdvisoryService(db)


Service = Annotated[AdvisoryService, Depends(get_service)]


# Usuario

@router.post("", response_model=AdvisoryOut, status_code=status.HTTP_201_CREATED)
def create_advisory(data: AdvisoryCreate, user: VerifiedUser, service: Service):
    return service.create(user, data)


@router.get("/me", response_model=Page[AdvisoryOut])
def list_my_advisories(
    user: CurrentUser, service: Service, page: PaginationDep, status: AdvisoryStatus | None = None
):
    return service.list_mine(user, page.skip, page.limit, status=status)


@router.get("/{advisory_id}", response_model=AdvisoryOut)
def read_advisory(advisory_id: int, user: CurrentUser, service: Service):
    return service.get(advisory_id, user)


@router.patch("/{advisory_id}", response_model=AdvisoryOut)
def update_advisory(advisory_id: int, data: AdvisoryUpdate, user: CurrentUser, service: Service):
    return service.update(advisory_id, user, data)


@router.post("/{advisory_id}/cancel", response_model=AdvisoryOut)
def cancel_advisory(advisory_id: int, user: CurrentUser, service: Service):
    return service.cancel(advisory_id, user)


# Asesores y administradores

@router.get("", response_model=Page[AdvisoryOut])
def list_advisories(
    _: StaffUser,
    service: Service,
    page: PaginationDep,
    status: AdvisoryStatus | None = None,
    advisor_id: int | None = None,
    unassigned: bool = False,
):
    return service.list_all(page.skip, page.limit, status=status, advisor_id=advisor_id, unassigned=unassigned)


@router.post("/{advisory_id}/assign", response_model=AdvisoryOut)
def assign_advisory(
    advisory_id: int,
    staff: StaffUser,
    service: Service,
    data: Annotated[AdvisoryAssign | None, Body()] = None,
):
    return service.assign(advisory_id, staff, data.advisor_id if data else None)


@router.post("/{advisory_id}/respond", response_model=AdvisoryOut)
def respond_advisory(
    advisory_id: int,
    data: AdvisoryRespond,
    staff: StaffUser,
    service: Service,
    background_tasks: BackgroundTasks,
):
    return service.respond(advisory_id, staff, data, background_tasks)


# Solo administradores

@router.patch("/{advisory_id}/status", response_model=AdvisoryOut)
def change_advisory_status(advisory_id: int, data: AdvisoryStatusUpdate, admin: AdminUser, service: Service):
    return service.change_status(advisory_id, admin, data.status)


@router.delete("/{advisory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_advisory(advisory_id: int, admin: AdminUser, service: Service):
    service.delete(advisory_id, admin)
