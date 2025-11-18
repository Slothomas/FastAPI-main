from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.db.sql_server_connection import get_session
from app.services.db import user_service

router = APIRouter(prefix="/users", tags=["Users"])


from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.db.sql_server_connection import get_session
from app.services.db import user_service

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
    """
    Crear un nuevo usuario.
    """
    existing_user = user_service.get_user_by_email(user_data.email, session)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    return user_service.create_new_user(user_data, session)



@router.get("/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    """
    Obtener lista de usuarios con paginación.
    """
    return user_service.get_all_users(skip, limit, session)


@router.get("/{email}", response_model=UserResponse)
def get_user_by_email(email: str, session: Session = Depends(get_session)):
    """
    Obtener un usuario específico por su email.
    """
    user = user_service.get_user_by_email(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email {email} no encontrado"
        )
    return user


@router.put("/{email}", response_model=UserResponse)
def update_user(email: str, user_data: UserUpdate, session: Session = Depends(get_session)):
    """
    Actualizar un usuario existente por email.
    """
    user = user_service.get_user_by_email(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email {email} no encontrado"
        )

    return user_service.update_existing_user(user, user_data, session)


@router.delete("/{email}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(email: str, session: Session = Depends(get_session)):
    """
    Eliminar un usuario por email (hard delete).
    """
    user = user_service.get_user_by_email(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email {email} no encontrado"
        )

    user_service.delete_user_permanently(user, session)
    return None


@router.patch("/{email}/deactivate", response_model=UserResponse)
def deactivate_user(email: str, session: Session = Depends(get_session)):
    """
    Desactivar un usuario por email (soft delete).
    """
    user = user_service.get_user_by_email(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email {email} no encontrado"
        )

    return user_service.deactivate_user_account(user, session)


@router.patch("/{email}/activate", response_model=UserResponse)
def activate_user(email: str, session: Session = Depends(get_session)):
    """
    Activar un usuario por email.
    """
    user = user_service.get_user_by_email(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email {email} no encontrado"
        )

    return user_service.activate_user_account(user, session)