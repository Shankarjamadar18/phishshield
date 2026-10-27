import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    database: Literal["up", "down"]


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
