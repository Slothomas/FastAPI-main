# app/controllers/login_controller.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.schemas.login import LoginRequest, LoginResponse
from app.services.db.sql_server_connection import get_session
from app.services.db import login_service

router = APIRouter(prefix="/login", tags=["Authentication"])


@router.post("", response_model=LoginResponse)
def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    """
    Autentica un usuario usando nombre de usuario o email + contraseña.

    La verificación de la contraseña se hace en login_service.authenticate_user,
    usando bcrypt (verify_password) contra el hash almacenado en la columna password.
    """

    user = login_service.authenticate_user(
        credentials.user,
        credentials.password,
        session,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario inactivo",
        )

    return LoginResponse(
        success=True,
        message="Login exitoso",
        user_id=user.id,
        email=user.email,
        user=user.user,
        role=user.user_type,
    )
