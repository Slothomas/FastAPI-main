from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.models.user import AppUser
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password


def get_user_by_email(email: str, session: Session) -> Optional[AppUser]:
    """
    Buscar un usuario por su email.
    Retorna None si no existe.
    """
    return session.exec(
        select(AppUser).where(AppUser.email == email)
    ).first()


def get_user_by_id(user_id: int, session: Session) -> Optional[AppUser]:
    """
    Buscar un usuario por su ID.
    Retorna None si no existe.
    """
    return session.get(AppUser, user_id)


def get_all_users(skip: int, limit: int, session: Session) -> List[AppUser]:
    """
    Obtener lista de usuarios con paginación.
    """
    users = session.exec(
        select(AppUser).order_by(AppUser.id).offset(skip).limit(limit)
    ).all()
    return list(users)


def create_new_user(user_data: UserCreate, session: Session) -> AppUser:
    """
    Crear un nuevo usuario en la base de datos.
    Hashea la contraseña antes de guardarla.
    """
    db_user = AppUser(
        user=user_data.user,
        email=user_data.email,
        password=hash_password(user_data.password),

        # ✅ NUEVO: guardar rut y user_type correctamente
        rut=user_data.rut,
        user_type=user_data.user_type,

        question1_id=user_data.question1_id,
        question1_answ=user_data.question1_answ,
        question2_id=user_data.question2_id,
        question2_answ=user_data.question2_answ,
        is_active=user_data.is_active,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


def update_existing_user(user: AppUser, user_data: UserUpdate, session: Session) -> AppUser:
    """
    Actualizar un usuario existente.
    Solo actualiza los campos que se envían.
    """
    user_dict = user_data.model_dump(exclude_unset=True)

    # Si se está actualizando la contraseña, hashearla
    if "password" in user_dict:
        user_dict["password"] = hash_password(user_dict["password"])

    # Actualizar el timestamp
    user_dict["updated_at"] = datetime.now()

    for key, value in user_dict.items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def delete_user_permanently(user: AppUser, session: Session) -> None:
    """
    Eliminar un usuario de la base de datos (hard delete).
    """
    session.delete(user)
    session.commit()


def deactivate_user_account(user: AppUser, session: Session) -> AppUser:
    """
    Desactivar un usuario (soft delete).
    Cambia is_active a 0.
    """
    user.is_active = 0
    user.updated_at = datetime.now()

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def activate_user_account(user: AppUser, session: Session) -> AppUser:
    """
    Activar un usuario.
    Cambia is_active a 1.
    """
    user.is_active = 1
    user.updated_at = datetime.now()

    session.add(user)
    session.commit()
    session.refresh(user)

    return user
