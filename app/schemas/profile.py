# app/schemas/profile.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    bio: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)
    skills: Optional[List[str]] = None
    avatar_url: Optional[str] = Field(None, max_length=500)

    # --- Nuevos campos gig ---
    region: Optional[str] = Field(None, max_length=100)
    comuna: Optional[str] = Field(None, max_length=100)

    availability_json: Optional[str] = None
    rate_hour: Optional[float] = Field(None, ge=0)
    min_shift_rate: Optional[float] = Field(None, ge=0)

    business_name: Optional[str] = Field(None, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)

    rating_avg: Optional[float] = None
    reviews_count: Optional[int] = None


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    # Convertir skills de string BD → lista API
    @field_validator("skills", mode="before")
    @classmethod
    def convert_skills_str_to_list(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v or []


class ProfileUpdate(ProfileBase):
    """
    Para actualizar el perfil de un usuario.
    """
    pass
