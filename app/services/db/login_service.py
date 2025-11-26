from typing import Optional
from sqlmodel import Session, select
from app.models.user import AppUser
from app.utils.security import verify_password


def authenticate_user(user_or_email: str, password: str, session: Session) -> Optional[AppUser]:
    """
    Autentica un usuario verificando usuario/email + contraseña hasheada.
    """

    # Buscar usuario por username o email
    user = session.exec(
        select(AppUser).where(
            (AppUser.user == user_or_email) | (AppUser.email == user_or_email)
        )
    ).first()

    if not user:
        return None

    if user.is_active == 0:
        return None

    # Verificación HASH bcrypt
    if not verify_password(password, user.password):
        return None

    return user
