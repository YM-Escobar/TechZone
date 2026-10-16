from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, PaginationDep, VerifiedUser
from app.Schema.common_schema import Page
from app.Schema.community_schema import (
    CommentCreate,
    CommentOut,
    CommentUpdate,
    PostCreate,
    PostOut,
    PostUpdate,
    ReportCreate,
    ReportOut,
)
from app.Services.community import CommunityService

router = APIRouter(tags=["comunidad"])


def get_service(db: DbSession) -> CommunityService:
    return CommunityService(db)


Service = Annotated[CommunityService, Depends(get_service)]


# Publicaciones

@router.get("/posts", response_model=Page[PostOut])
def list_posts(service: Service, page: PaginationDep, search: str | None = None, author_id: int | None = None):
    return service.list_posts(page.skip, page.limit, search=search, author_id=author_id)


@router.get("/posts/{post_id}", response_model=PostOut)
def read_post(post_id: int, service: Service):
    return service.get_post(post_id)


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, user: VerifiedUser, service: Service):
    return service.create_post(user, data)


@router.patch("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, data: PostUpdate, user: CurrentUser, service: Service):
    return service.update_post(post_id, user, data)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, user: CurrentUser, service: Service):
    service.delete_post(post_id, user)


@router.post("/posts/{post_id}/like", response_model=PostOut)
def like_post(post_id: int, user: CurrentUser, service: Service):
    return service.like_post(post_id, user)


@router.delete("/posts/{post_id}/like", response_model=PostOut)
def unlike_post(post_id: int, user: CurrentUser, service: Service):
    return service.unlike_post(post_id, user)


# Comentarios

@router.get("/posts/{post_id}/comments", response_model=Page[CommentOut])
def list_comments(post_id: int, service: Service, page: PaginationDep):
    return service.list_comments(post_id, page.skip, page.limit)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(post_id: int, data: CommentCreate, user: VerifiedUser, service: Service):
    return service.add_comment(post_id, user, data)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(comment_id: int, data: CommentUpdate, user: CurrentUser, service: Service):
    return service.update_comment(comment_id, user, data)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, user: CurrentUser, service: Service):
    service.delete_comment(comment_id, user)


# Reportes (los revisa el admin en /admin/reports)

@router.post("/posts/{post_id}/report", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def report_post(post_id: int, data: ReportCreate, user: CurrentUser, service: Service):
    return service.report_post(post_id, user, data)


@router.post("/comments/{comment_id}/report", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def report_comment(comment_id: int, data: ReportCreate, user: CurrentUser, service: Service):
    return service.report_comment(comment_id, user, data)
