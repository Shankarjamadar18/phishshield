import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class DependencyStatus(BaseModel):
    status: Literal["up", "down"]
    error: str | None = None


class ReadyOut(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: dict[str, DependencyStatus]


class ScanCreate(BaseModel):
    scan_type: Literal["url", "email", "text"]
    input_value: str = Field(min_length=1, max_length=20000)


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    scan_type: str
    input_value: str
    status: str
    verdict: str | None
    risk_score: float | None
    created_at: datetime
