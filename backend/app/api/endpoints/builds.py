from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, OptionalUser, PaginationDep
from app.Schema.build_schema import BuildCreate, BuildOut, BuildUpdate
from app.Schema.common_schema import Page
from app.Services.builds import BuildService

router = APIRouter(prefix="/builds", tags=["builds"])


def get_service(db: DbSession) -> BuildService:
    return BuildService(db)


Service = Annotated[BuildService, Depends(get_service)]


@router.get("/public", response_model=Page[BuildOut])
def list_public_builds(service: Service, page: PaginationDep, search: str | None = None):
    return service.list_public(page.skip, page.limit, search=search)


@router.get("/me", response_model=Page[BuildOut])
def list_my_builds(user: CurrentUser, service: Service, page: PaginationDep):
    return service.list_mine(user, page.skip, page.limit)


@router.get("/{build_id}", response_model=BuildOut)
def read_build(build_id: int, viewer: OptionalUser, service: Service):
    return service.get(build_id, viewer)


@router.post("", response_model=BuildOut, status_code=status.HTTP_201_CREATED)
def create_build(data: BuildCreate, user: CurrentUser, service: Service):
    return service.create(user, data)


@router.patch("/{build_id}", response_model=BuildOut)
def update_build(build_id: int, data: BuildUpdate, user: CurrentUser, service: Service):
    return service.update(build_id, user, data)


@router.delete("/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_build(build_id: int, user: CurrentUser, service: Service):
    service.delete(build_id, user)


@router.post("/{build_id}/clone", response_model=BuildOut, status_code=status.HTTP_201_CREATED)
def clone_build(build_id: int, user: CurrentUser, service: Service):
    return service.clone(build_id, user)
