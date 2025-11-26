# app/controllers/auth_controller.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.dependencies import get_current_user
from app.services.db.sql_server_connection import get_session
from app.models.user import AppUser
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    payload: ChangePasswordIn,
    session: Session = Depends(get_session),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Cambia la contraseña del usuario autenticado.
    Usa la contraseña actual para validar, y luego actualiza con un nuevo hash.
    """

    # 1) Validar contraseña actual
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    # 2) Reglas mínimas (ya validas en front, pero reforzamos acá)
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 8 caracteres",
        )

    # 3) Actualizar hash + updated_at
    current_user.password = hash_password(payload.new_password)
    current_user.updated_at = datetime.now()

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"message": "Contraseña actualizada correctamente"}
