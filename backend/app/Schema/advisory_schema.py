from datetime import datetime

from pydantic import BaseModel, Field

from app.Models.advisory import AdvisoryPurpose, AdvisoryStatus
from app.Schema.build_schema import BuildOut
from app.Schema.common_schema import Money, ORMModel
from app.Schema.user_schema import UserSummary


class AdvisoryCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    purpose: AdvisoryPurpose
    budget: Money = Field(gt=0, max_digits=10, decimal_places=2)
    preferences: str | None = Field(default=None, max_length=5000)


class AdvisoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    purpose: AdvisoryPurpose | None = None
    budget: Money | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    preferences: str | None = Field(default=None, max_length=5000)


class AdvisoryAssign(BaseModel):
    # Vacío = el asesor se asigna a sí mismo; un admin puede indicar otro asesor
    advisor_id: int | None = None


class AdvisoryRespond(BaseModel):
    advisor_notes: str = Field(min_length=1, max_length=10000)
    recommended_build_id: int | None = None


class AdvisoryStatusUpdate(BaseModel):
    status: AdvisoryStatus


class AdvisoryOut(ORMModel):
    id: int
    title: str
    purpose: AdvisoryPurpose
    budget: Money
    preferences: str | None
    status: AdvisoryStatus
    user: UserSummary
    advisor: UserSummary | None
    advisor_notes: str | None
    recommended_build: BuildOut | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
