# app/schemas/certificate.py
from datetime import datetime
from pydantic import BaseModel

class CertificateResponse(BaseModel):
    """
    Respuesta al listar o subir un certificado.
    No exponemos rutas internas, solo el nombre original.
    """
    id: int
    user_id: int
    file_name_original: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# --- AÑADE ESTA NUEVA CLASE AL FINAL ---
class CertificateDownloadResponse(BaseModel):
    """
    Respuesta al pedir un enlace de descarga.
    """
    download_url: str