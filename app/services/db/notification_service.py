from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from sqlmodel import Session, select

from app.models.notification import Notification


class NotificationService:

    @staticmethod
    def create_notification(
        session: Session,
        user_id: int,
        type: str,
        payload: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,   # <--- NUEVO
        message: Optional[str] = None  # <--- NUEVO
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,      # Asignamos title
            message=message,  # Asignamos message
            payload=json.dumps(payload) if payload else None,
            is_read=False,
            created_at=datetime.utcnow(),
            is_active=True
        )
        session.add(notif)
        session.commit()
        session.refresh(notif)
        return notif

    @staticmethod
    def list_notifications(session: Session, user_id: int, only_unread: bool = False) -> List[Notification]:
        q = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_active == True
        )

        if only_unread:
            q = q.where(Notification.is_read == False)

        q = q.order_by(Notification.created_at.desc())
        return session.exec(q).all()

    @staticmethod
    def mark_as_read(session: Session, notification_id: int, user_id: Optional[int] = None) -> Optional[Notification]:
        """
        Marca como leída.
        user_id es Opcional: Si viene None, saltamos la validación de dueño (útil para llamadas simples del frontend).
        """
        notif = session.get(Notification, notification_id)
        if not notif:
            return None
            
        # Solo validamos dueño si se proporciona el user_id
        if user_id is not None and notif.user_id != user_id:
            return None

        notif.is_read = True
        session.add(notif)
        session.commit()
        session.refresh(notif)
        return notif

    @staticmethod
    def delete_notification(session: Session, notification_id: int, user_id: Optional[int] = None) -> bool:
        """
        Borrado lógico (soft delete).
        user_id es Opcional.
        """
        notif = session.get(Notification, notification_id)
        if not notif:
            return False
            
        # Solo validamos dueño si se proporciona el user_id
        if user_id is not None and notif.user_id != user_id:
            return False

        notif.is_active = False
        session.add(notif)
        session.commit()
        return True