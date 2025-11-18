# app/schemas/support.py
from pydantic import BaseModel, EmailStr

class SupportTicket(BaseModel):
    user_email: EmailStr
    subject: str
    message: str