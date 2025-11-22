# app/schemas/job_offer.py
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

from app.models.job_offer import JobType, JobOfferStatus, UrgencyType


class JobOfferCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=200)
    job_type: JobType
    description: str = Field(..., min_length=10)

    salary_range: Optional[str] = Field(None, max_length=100)
    requirements: Optional[str] = None

    # nuevos gig
    required_skills: Optional[str] = None
    urgency: Optional[UrgencyType] = UrgencyType.NORMAL
    status: Optional[JobOfferStatus] = JobOfferStatus.PUBLICADO
    region: Optional[str] = None
    comuna: Optional[str] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None


class JobOfferUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    job_type: Optional[JobType] = None
    description: Optional[str] = Field(None, min_length=10)
    salary_range: Optional[str] = Field(None, max_length=100)
    requirements: Optional[str] = None

    # gig updateables
    required_skills: Optional[str] = None
    urgency: Optional[UrgencyType] = None
    status: Optional[JobOfferStatus] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None

    is_active: Optional[int] = Field(None, ge=0, le=1)


class JobOfferResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    job_type: JobType
    description: str

    salary_range: Optional[str]
    requirements: Optional[str]

    required_skills: Optional[str]
    urgency: UrgencyType
    status: JobOfferStatus
    region: Optional[str]
    comuna: Optional[str]
    date_start: Optional[date]
    date_end: Optional[date]

    created_by: int
    selected_application_id: Optional[int] = None
    filled_at: Optional[datetime] = None

    is_active: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


class JobOfferWithApplications(JobOfferResponse):
    applications_count: int = 0
