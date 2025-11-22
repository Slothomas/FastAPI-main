from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# Schema para crear un usuario (sin id, sin timestamps)
class UserCreate(BaseModel):
    user: str = Field(..., min_length=1, max_length=50, description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, max_length=72, description="Contraseña del usuario (máx 72 caracteres por límite de bcrypt)")
    user_type: Optional[str] = Field(None, max_length=512, description="Clave adicional")
    question1_id: Optional[int] = Field(None, ge=0, le=255, description="ID de pregunta de seguridad 1")
    question1_answ: Optional[str] = Field(None, max_length=255, description="Respuesta a pregunta 1")
    question2_id: Optional[int] = Field(None, ge=0, le=255, description="ID de pregunta de seguridad 2")
    question2_answ: Optional[str] = Field(None, max_length=255, description="Respuesta a pregunta 2")
    is_active: int = Field(1, ge=0, le=1, description="Usuario activo (1=activo, 0=inactivo)")

# Schema para actualizar un usuario (todos los campos opcionales excepto el que se quiera actualizar)
class UserUpdate(BaseModel):
    user: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=72)
    user_type: Optional[str] = Field(None, max_length=512)
    question1_id: Optional[int] = Field(None, ge=0, le=255)
    question1_answ: Optional[str] = Field(None, max_length=255)
    question2_id: Optional[int] = Field(None, ge=0, le=255)
    question2_answ: Optional[str] = Field(None, max_length=255)
    is_active: Optional[int] = Field(None, ge=0, le=1, description="1=activo, 0=inactivo")

# Schema para la respuesta (incluye todos los campos, sin password)
class UserResponse(BaseModel):
    id: int
    user: str
    email: str
    user_type: Optional[str] = None
    question1_id: Optional[int] = None
    question1_answ: Optional[str] = None
    question2_id: Optional[int] = None
    question2_answ: Optional[str] = None
    is_active: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
