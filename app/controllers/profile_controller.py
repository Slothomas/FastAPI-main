from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session


from app.services.storage import certificate_service as storage_service
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.db.sql_server_connection import get_session
from app.services.db import profile_service

router = APIRouter(prefix="/users", tags=["Profile"])

# --- Ruta para obtener el perfil ---
@router.get("/{user_id}/profile", response_model=ProfileResponse)
def get_user_profile(
    user_id: int,
    session: Session = Depends(get_session),
):
    profile = profile_service.get_profile_by_user_id(user_id, session)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado para este usuario",
        )
    return profile

# --- Ruta para crear o actualizar el perfil ---
@router.put("/{user_id}/profile", response_model=ProfileResponse)
def upsert_user_profile(
    user_id: int,
    data: ProfileUpdate,
    session: Session = Depends(get_session),
):
    profile = profile_service.upsert_profile(user_id, data, session)
    return profile

# --- NUEVA RUTA: Subida de Avatares ---
@router.post("/{user_id}/avatar", response_model=ProfileResponse)
def upload_user_avatar(
    user_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Sube un nuevo avatar para un usuario.
    El archivo debe enviarse como 'multipart/form-data'.
    """
    try:
        # Llama a la nueva función de servicio
        storage_service.upload_avatar_to_blob(
            user_id=user_id,
            file=file,
            session=session
        )
        
        # Devuelve el perfil completo actualizado
        return profile_service.get_profile_by_user_id(user_id, session)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))