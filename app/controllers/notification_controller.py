import traceback
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
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
    try:
        notif = NotificationService.create_notification(
            session=session,
            user_id=data.user_id,
            type=data.type,
            payload=data.payload,
            title=getattr(data, "title", None),
            message=getattr(data, "message", None)
        )
        return NotificationResponse.from_model(notif)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
def list_notifications(
    user_id: int,
    only_unread: bool = Query(False, description="Solo no leídas"),
    session: Session = Depends(get_session)
):
    """
    Obtener notificaciones. Usa JSONResponse para evitar error 422/500 por Enums.
    """
    try:
        notifs = NotificationService.list_notifications(session, user_id, only_unread)
        
        # Serialización manual segura
        data = []
        for n in notifs:
            safe_type = str(n.type.value) if hasattr(n.type, 'value') else str(n.type)
            data.append({
                "id": n.id,
                "user_id": n.user_id,
                "type": safe_type,
                "title": getattr(n, "title", None),
                "message": getattr(n, "message", None),
                "payload": n.payload,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            })
            
        return JSONResponse(content=jsonable_encoder(data))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    # FIX: Hacemos user_id OPCIONAL porque el frontend no lo envía
    user_id: Optional[int] = Query(None, description="ID del usuario dueño"),
    session: Session = Depends(get_session)
):
    try:
        # Si tu servicio requiere user_id obligatoriamente, esto podría fallar si user_id es None.
        # Idealmente el servicio debería ser capaz de marcar leída solo con el ID de la notificación.
        notif = NotificationService.mark_as_read(session, notification_id, user_id)
        
        if not notif:
            raise HTTPException(404, "Notificación no encontrada")
            
        # Respuesta simple JSON
        return JSONResponse(content={"success": True, "id": notif.id, "is_read": True})
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    # FIX: Hacemos user_id OPCIONAL
    user_id: Optional[int] = Query(None, description="ID del usuario dueño"),
    session: Session = Depends(get_session)
):
    try:
        ok = NotificationService.delete_notification(session, notification_id, user_id)
        if not ok:
            raise HTTPException(404, "Notificación no encontrada")
        return None
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))