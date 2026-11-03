from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from app.Models.user import UserRole
from app.Schema.common_schema import ORMModel

Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserCreate(BaseModel):
    email: EmailStr
    username: Username
    full_name: str | None = Field(default=None, max_length=120)
    password: Password


class AdminUserCreate(UserCreate):
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    username: Username | None = None
    full_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=1000)
    avatar_url: str | None = Field(default=None, max_length=500)


class AdminUserUpdate(UserUpdate):
    email: EmailStr | None = None
    is_verified: bool | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: Password


class RoleUpdate(BaseModel):
    role: UserRole


class StatusUpdate(BaseModel):
    is_active: bool


class UserSummary(ORMModel):
    id: int
    username: str
    full_name: str | None
    avatar_url: str | None


class UserPublic(UserSummary):
    role: UserRole
    bio: str | None
    created_at: datetime


class UserOut(UserPublic):
    email: EmailStr
    is_active: bool
    is_verified: bool
    updated_at: datetime


class UserStats(BaseModel):
    total: int
    active: int
    inactive: int
    by_role: dict[str, int]


class AdminStats(BaseModel):
    users: UserStats
    products: int
    builds: int
    posts: int
    comments: int
    pending_reports: int
    advisories_by_status: dict[str, int]
