# app/controllers/certificate_controller.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response 
from sqlmodel import Session

from app.services.db.sql_server_connection import get_session
from app.schemas.certificate import CertificateResponse, CertificateDownloadResponse
from app.services.storage import certificate_service 

# --- Router 1: Para subir y listar (depende del user_id) ---
router = APIRouter(prefix="/users/{user_id}/certificates", tags=["Certificates"])

@router.post("", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def upload_certificate(
    user_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    try:
        certificate = certificate_service.upload_certificate_to_blob(
            user_id=user_id,
            file=file,
            session=session
        )
        return certificate
    except Exception as e:
        raise e

@router.get("", response_model=List[CertificateResponse])
def get_user_certificates(
    user_id: int,
    session: Session = Depends(get_session)
):
    certificates = certificate_service.get_certificates_for_user(user_id, session)
    return certificates


# --- Router 2: Para descargar y eliminar (depende del certificate_id) ---
router_download = APIRouter(prefix="/certificates", tags=["Certificates"])

@router_download.get("/{certificate_id}/download", response_model=CertificateDownloadResponse)
def get_certificate_download_link(
    certificate_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtiene un enlace de descarga SAS temporal (1 hora) para un certificado.
    """
    try:
        url_dict = certificate_service.get_download_url_for_certificate(
            certificate_id=certificate_id,
            session=session
        )
        return url_dict
    except Exception as e:
        raise e
    

@router_download.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    certificate_id: int,
    session: Session = Depends(get_session)
):
    """
    Desactiva (soft delete) un certificado.
    """
    try:
        certificate_service.deactivate_certificate(
            certificate_id=certificate_id,
            session=session
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise e