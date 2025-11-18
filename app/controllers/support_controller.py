# app/controllers/support_controller.py
from fastapi import APIRouter, Depends, status
from app.schemas.support import SupportTicket
from app.services import email_service

router = APIRouter(prefix="/support", tags=["Support"])

@router.post("", status_code=status.HTTP_202_ACCEPTED)
def submit_support_ticket(ticket: SupportTicket):
    """
    Recibe un ticket de soporte desde el frontend
    y usa el email_service para enviarlo.
    """
    try:
        email_service.send_support_email(ticket)
        return {"message": "Ticket de soporte enviado correctamente."}
    except Exception as e:
        # El email_service ya levanta un HTTPException,
        # así que esto lo captura y lo devuelve al front.
        raise e