from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.schemas.login import LoginRequest, LoginResponse
from app.services.db.sql_server_connection import get_session
from app.services.db import login_service

router = APIRouter(prefix="/login", tags=["Authentication"])


@router.post("", response_model=LoginResponse)
def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    """
    Autenticar un usuario con nombre de usuario/email y contraseña.

    Verifica las credenciales del usuario y retorna información básica si son correctas.
    """
    # Intentar autenticar al usuario
    user = login_service.authenticate_user(
        credentials.user,
        credentials.password,
        session
    )

    # Si las credenciales son incorrectas o el usuario no existe
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario inactivo"
        )

    # Retornar respuesta exitosa
    return LoginResponse(
        success=True,
        message="Login exitoso",
        user_id=user.id,
        email=user.email,
        user=user.user,
        role=user.clave  
    )
