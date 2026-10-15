"""
CareDose AI — Pydantic Request/Response Schemas (backend/schemas.py)
"""

from typing import Optional
from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)


class MedicationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    dosage: str = Field(..., min_length=1, max_length=60)
    frequency: str = Field(default="Once Daily", min_length=1, max_length=60)
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    instructions: Optional[str] = Field(default="", max_length=250)


class MedicationUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    dosage: str = Field(..., min_length=1, max_length=60)
    frequency: str = Field(default="Once Daily", min_length=1, max_length=60)
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    instructions: Optional[str] = Field(default="", max_length=250)


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(taken|missed|pending)$")
    scheduled_date: Optional[str] = None


class FollowUpResponseRequest(BaseModel):
    medication_id: int
    response_choice: str = Field(..., pattern=r"^(yes_taken|not_yet|not_sure)$")
    scheduled_date: Optional[str] = None


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class CaregiverUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    contact: str = Field(..., min_length=3, max_length=150)
    relationship: Optional[str] = Field(default="Family Member", max_length=80)
    enabled: bool = Field(default=False)
    alert_threshold: int = Field(default=2, ge=1, le=10)
    consent_given: bool = Field(default=False)


class SettingsUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    notifications_enabled: bool = Field(default=True)
    follow_up_delay_minutes: int = Field(default=30, ge=5, le=240)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
