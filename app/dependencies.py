from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select
from app.services.db.sql_server_connection import get_session
from app.models.user import AppUser


def get_current_user(
    session: Session = Depends(get_session),
    authorization: str = Header(default=None, alias="Authorization"),
    x_user_id: int = Header(default=None, alias="X-UserID"),
):
    """
    Obtiene el usuario actual basado en un header simple.
    Soporta ambas formas:
      Authorization: UserID <id>
      X-UserID: <id>
    """

    # Si viene X-UserID, este tiene prioridad
    if x_user_id is not None:
        user = session.exec(select(AppUser).where(AppUser.id == x_user_id)).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )
        return user

    # Si no viene X-UserID, usamos Authorization: UserID <id>
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="No autenticado"
        )

    parts = authorization.split()

    # Formato esperado → "UserID <id>"
    if len(parts) == 2 and parts[0].lower() == "userid":
        try:
            user_id = int(parts[1])
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="ID de usuario inválido"
            )

        user = session.exec(select(AppUser).where(AppUser.id == user_id)).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        return user

    # Si Authorization existe pero no cumple el formato
    raise HTTPException(
        status_code=401,
        detail="Formato de Authorization inválido. Use 'Authorization: UserID <id>'"
    )
