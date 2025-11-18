# app/services/email_service.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException
from app.schemas.support import SupportTicket

# !! IMPORTANTE !!
# 1. Cambia esto por tu email (el que usaste para registrarte en SendGrid).
# 2. Debes "Verificar" este email en el portal de SendGrid para que funcione.
MY_SUPPORT_EMAIL = "josetomas.guzman10@gmail.com"


def send_support_email(ticket: SupportTicket):
    API_KEY = os.getenv("SENDGRID_API_KEY")
    if not API_KEY:
        print("ERROR: SENDGRID_API_KEY no está configurada.")
        raise HTTPException(status_code=500, detail="Servicio de email no configurado.")
        
    # Creamos el contenido del email que TÚ vas a recibir
    html_content = f"""
    <h3>Nuevo ticket de soporte desde BaristaApp:</h3>
    <p><strong>De:</strong> {ticket.user_email}</p>
    <p><strong>Asunto:</strong> {ticket.subject}</p>
    <hr>
    <p>{ticket.message.replace(chr(10), '<br>')}</p>
    """

    message = Mail(
        from_email=MY_SUPPORT_EMAIL, # El remitente (tú)
        to_emails=MY_SUPPORT_EMAIL,  # El destinatario (tú)
        subject=f"Soporte BaristaApp: {ticket.subject}",
        html_content=html_content
    )
    
    # Le decimos a SendGrid que el "reply-to" sea el email del usuario
    # para que puedas presionar "Responder" en tu Gmail.
    message.reply_to = ticket.user_email

    try:
        sg = SendGridAPIClient(API_KEY)
        response = sg.send(message)
        
        # Opcional: imprimir el log para ver que funcionó
        print(f"Email enviado, status code: {response.status_code}")
        return response
    except Exception as e:
        print(f"Error al enviar email: {e}")
        raise HTTPException(status_code=500, detail=f"Error al enviar el email: {str(e)}")