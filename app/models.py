from typing import Any
from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    user_id: str
    role: str
    tenant_id: str
    purpose_of_use: str
    patient_context: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class InvokeResponse(BaseModel):
    output: str
    status: str
    policy_decision: str
    trace_id: str
    review_id: str | None = None


class HealthResponse(BaseModel):
    status: str


class ReviewDecisionRequest(BaseModel):
    approved: bool
    reviewer_id: str
    reason: str | None = None


class ReviewResponse(BaseModel):
    review_id: str
    status: str
    message: str
