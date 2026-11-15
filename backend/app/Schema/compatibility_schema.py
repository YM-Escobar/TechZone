from typing import Literal

from pydantic import BaseModel, ConfigDict


class CompatibilityRuleResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    status: Literal["compatible", "incompatible", "warning"]
    message: str
    components: list[str]


class BuildCompatibilityResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Literal["compatible", "incompatible", "warning", "review_required"]
    is_compatible: bool
    summary: str
    total_rules: int
    compatible_count: int
    incompatible_count: int
    warning_count: int
    results: list[CompatibilityRuleResultOut]
