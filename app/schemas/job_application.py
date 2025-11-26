# app/schemas/job_application.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.job_application import ApplicationStatus
import json


class JobApplicationCreate(BaseModel):
    job_offer_id: int = Field(..., gt=0, description="ID de la oferta de trabajo")
    cover_letter: Optional[str] = Field(None, description="Carta de presentación")


class JobApplicationUpdateStatus(BaseModel):
    status: str = Field(..., description="Estado de la postulación (lowercase)")
    recruiter_notes: Optional[str] = Field(None, description="Notas del reclutador")

    # rechazo
    rejection_reason: Optional[str] = None
    rejection_note: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: int
    job_offer_id: int
    user_id: int
    cover_letter: Optional[str]
    status: ApplicationStatus
    recruiter_notes: Optional[str]

    match_score: Optional[float] = None
    match_breakdown: Optional[Dict[str, Any]] = None
    match_refreshed_at: Optional[datetime] = None

    applied_at: datetime
    updated_at: datetime

    rejection_reason: Optional[str] = None
    rejection_note: Optional[str] = None
    rejected_at: Optional[datetime] = None

    # ============================
    # NUEVOS CAMPOS PARA RESEÑAS
    # (deben existir en el modelo/tabla job_application)
    # ============================
    worker_reviewed: bool = False
    employer_reviewed: bool = False

    class Config:
        from_attributes = True
        use_enum_values = True

    @classmethod
    def from_model(cls, app):
        breakdown = None
        if getattr(app, "match_breakdown_json", None):
            try:
                breakdown = json.loads(app.match_breakdown_json)
            except Exception:
                breakdown = None

        return cls(
            id=app.id,
            job_offer_id=app.job_offer_id,
            user_id=app.user_id,
            cover_letter=app.cover_letter,
            status=app.status,
            recruiter_notes=app.recruiter_notes,
            match_score=float(app.match_score) if app.match_score is not None else None,
            match_breakdown=breakdown,
            match_refreshed_at=app.match_refreshed_at,
            applied_at=app.applied_at,
            updated_at=app.updated_at,

            rejection_reason=app.rejection_reason,
            rejection_note=app.rejection_note,
            rejected_at=app.rejected_at,

            worker_reviewed=bool(getattr(app, "worker_reviewed", False)),
            employer_reviewed=bool(getattr(app, "employer_reviewed", False)),
        )


class JobApplicationWithUser(JobApplicationResponse):
    user_name: str
    user_email: str
    user_cv_summary: Optional[str] = None


class JobApplicationWithOffer(JobApplicationResponse):
    job_title: str
    company: str
    location: str
    job_offer_salary_range: Optional[int] = None
    employer_id: Optional[int] = None
