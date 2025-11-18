# app/models/user_certificate.py

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserCertificate(SQLModel, table=True):
    __tablename__ = "app_user_certificate"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)

    # El nombre que el usuario le dio al archivo
    file_name_original: str = Field(max_length=255)

    # El "camino" o nombre único que le dimos en Blob Storage
    storage_path: str = Field(max_length=1000)

    # Para saber qué tipo de archivo es (PDF, JPG, etc.)
    content_type: str = Field(max_length=100)
    
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # 1 para activo, 0 para inactivo (borrado lógico)
    is_active: int = Field(default=1, nullable=False)