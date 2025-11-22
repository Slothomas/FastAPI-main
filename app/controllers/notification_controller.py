from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from sqlmodel import Session

from app.services.db.sql_server_connection import get_session
from app.services.db.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationMarkRead
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    data: NotificationCreate,
    session: Session = Depends(get_session)
):
    notif = NotificationService.create_notification(
        session=session,
        user_id=data.user_id,
        type=data.type,
        payload=data.payload
    )
    return NotificationResponse.from_model(notif)


@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def list_notifications(
    user_id: int,
    only_unread: bool = Query(False, description="Solo no leídas"),
    session: Session = Depends(get_session)
):
    notifs = NotificationService.list_notifications(session, user_id, only_unread)
    return [NotificationResponse.from_model(n) for n in notifs]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    user_id: int = Query(..., description="ID del usuario dueño"),
    session: Session = Depends(get_session)
):
    notif = NotificationService.mark_as_read(session, notification_id, user_id)
    if not notif:
        raise HTTPException(404, "Notificación no encontrada")
    return NotificationResponse.from_model(notif)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    user_id: int = Query(..., description="ID del usuario dueño"),
    session: Session = Depends(get_session)
):
    ok = NotificationService.delete_notification(session, notification_id, user_id)
    if not ok:
        raise HTTPException(404, "Notificación no encontrada")
    return None
