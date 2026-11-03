from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import AdminUser, DbSession, PaginationDep
from app.Models.community import ReportStatus
from app.Models.user import UserRole
from app.Schema.common_schema import Page
from app.Schema.community_schema import CommentOut, ReportOut, ReportStatusUpdate
from app.Schema.user_schema import (
    AdminStats,
    AdminUserCreate,
    AdminUserUpdate,
    RoleUpdate,
    StatusUpdate,
    UserOut,
)
from app.Services.admin import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_service(db: DbSession) -> AdminService:
    return AdminService(db)


Service = Annotated[AdminService, Depends(get_service)]


@router.get("/stats", response_model=AdminStats)
def read_stats(_: AdminUser, service: Service):
    return service.stats()


@router.get("/users", response_model=Page[UserOut])
def list_users(
    _: AdminUser,
    service: Service,
    page: PaginationDep,
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
):
    return service.list_users(page.skip, page.limit, search=search, role=role, is_active=is_active)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(data: AdminUserCreate, _: AdminUser, service: Service):
    return service.create_user(data)


@router.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int, _: AdminUser, service: Service):
    return service.get_user(user_id)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: AdminUserUpdate, _: AdminUser, service: Service):
    return service.update_user(user_id, data)


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_role(user_id: int, data: RoleUpdate, admin: AdminUser, service: Service):
    return service.change_role(admin, user_id, data.role)


@router.patch("/users/{user_id}/status", response_model=UserOut)
def change_status(user_id: int, data: StatusUpdate, admin: AdminUser, service: Service):
    return service.set_status(admin, user_id, data.is_active)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, admin: AdminUser, service: Service):
    service.delete_user(admin, user_id)


# Moderación: el contenido se elimina con DELETE /posts/{id} y DELETE /comments/{id}

@router.get("/comments", response_model=Page[CommentOut])
def list_comments(
    _: AdminUser, service: Service, page: PaginationDep, search: str | None = None, author_id: int | None = None
):
    return service.list_comments(page.skip, page.limit, search=search, author_id=author_id)


@router.get("/reports", response_model=Page[ReportOut])
def list_reports(_: AdminUser, service: Service, page: PaginationDep, status: ReportStatus | None = None):
    return service.list_reports(page.skip, page.limit, status=status)


@router.patch("/reports/{report_id}", response_model=ReportOut)
def update_report(report_id: int, data: ReportStatusUpdate, admin: AdminUser, service: Service):
    return service.update_report_status(admin, report_id, data.status)
