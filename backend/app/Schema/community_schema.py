from datetime import datetime

from pydantic import BaseModel, Field

from app.Models.community import ReportStatus
from app.Schema.common_schema import ORMModel
from app.Schema.user_schema import UserSummary


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1, max_length=10000)
    build_id: int | None = None


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    build_id: int | None = None


class PostOut(ORMModel):
    id: int
    title: str
    content: str
    author: UserSummary
    build_id: int | None
    comment_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentUpdate(CommentCreate):
    pass


class CommentOut(ORMModel):
    id: int
    post_id: int
    content: str
    author: UserSummary
    created_at: datetime
    updated_at: datetime


class ReportCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class ReportStatusUpdate(BaseModel):
    status: ReportStatus


class PostSummary(ORMModel):
    id: int
    title: str
    author: UserSummary


class ReportOut(ORMModel):
    id: int
    reason: str
    status: ReportStatus
    reporter: UserSummary
    post: PostSummary | None
    comment: CommentOut | None
    resolved_by: UserSummary | None
    resolved_at: datetime | None
    created_at: datetime
