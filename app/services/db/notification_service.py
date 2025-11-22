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
        payload: Optional[Dict[str, Any]] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
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
        return list(session.exec(q).all())

    @staticmethod
    def mark_as_read(session: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        notif = session.get(Notification, notification_id)
        if not notif or notif.user_id != user_id:
            return None

        notif.is_read = True
        session.add(notif)
        session.commit()
        session.refresh(notif)
        return notif

    @staticmethod
    def delete_notification(session: Session, notification_id: int, user_id: int) -> bool:
        notif = session.get(Notification, notification_id)
        if not notif or notif.user_id != user_id:
            return False

        notif.is_active = False
        session.add(notif)
        session.commit()
        return True
