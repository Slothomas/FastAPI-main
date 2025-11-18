# app/schemas/profile.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator  # <--- 1. Importa field_validator


class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    bio: Optional[str] = None
    years_experience: Optional[int] = Field(None, ge=0)
    skills: Optional[List[str]] = None       # en la API como lista
    avatar_url: Optional[str] = Field(None, max_length=500)


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Esto le dice a Pydantic que lea desde el objeto de BD

    # --- 2. AÑADE ESTE CÓDIGO ---
    @field_validator("skills", mode="before")
    @classmethod
    def convert_skills_str_to_list(cls, v):
        """
        Este validador se ejecuta ANTES de la validación.
        Toma el valor del objeto de la BD (v) y lo transforma.
        """
        if isinstance(v, str):
            # Si es un string, lo convierte en lista
            return [s.strip() for s in v.split(',') if s.strip()]
        if v is None:
            # Si es None, devuelve una lista vacía (o None, si lo prefieres)
            return []
        # Si ya es una lista (por alguna razón), la devuelve tal cual
        return v
    # --- FIN DEL CÓDIGO NUEVO ---


class ProfileUpdate(ProfileBase):
    """
    Para actualizar el perfil de un usuario.
    Todos los campos opcionales (PATCH/PUT tipo upsert).
    """
    pass
