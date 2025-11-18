# app/services/storage/certificate_service.py
import os
import uuid
from datetime import datetime, timedelta  # <-- 1. Importa timedelta
from fastapi import UploadFile, HTTPException
from sqlmodel import Session, select
from azure.storage.blob import (  # <-- 2. Importa estos
    BlobServiceClient, 
    BlobSasPermissions, 
    generate_blob_sas
)
from dotenv import load_dotenv


from app.services.db import profile_service
from app.models.user_certificate import UserCertificate

# ... (Carga de load_dotenv) ...

# --- Configuración de Blob Storage ---
try:
    CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not CONNECTION_STRING:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING no está configurada")
        
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    CONTAINER_NAME = "baristapp-certificados" # El nombre que creaste en Azure
    
    # Obtenemos el nombre de la cuenta para generar el SAS
    ACCOUNT_NAME = blob_service_client.account_name

except Exception as e:
    print(f"ERROR: No se pudo conectar a Blob Storage. {e}")
    blob_service_client = None
    ACCOUNT_NAME = None
# --- Fin Configuración ---


def upload_certificate_to_blob(user_id: int, file: UploadFile, session: Session) -> UserCertificate:
    # ... (Esta función se queda igual que antes) ...
    if not blob_service_client:
        raise HTTPException(status_code=500, detail="Servicio de almacenamiento no configurado.")
    # 1. Generar un nombre único...
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"user_{user_id}_{uuid.uuid4()}{file_extension}"
    try:
        # 2. Subir el archivo al blob...
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=unique_filename)
        blob_client.upload_blob(file.file, blob_type="BlockBlob")
        # 3. Guardar la metadata en la base de datos SQL...
        db_certificate = UserCertificate(
            user_id=user_id,
            file_name_original=file.filename,
            storage_path=unique_filename,
            content_type=file.content_type
        )
        session.add(db_certificate)
        session.commit()
        session.refresh(db_certificate)
        return db_certificate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el proceso de subida: {str(e)}")


def get_certificates_for_user(user_id: int, session: Session) -> list[UserCertificate]:
    # ... (Esta función se queda igual que antes) ...
    stmt = select(UserCertificate).where(UserCertificate.user_id == user_id, UserCertificate.is_active == 1  # <-- Añade este filtro
                                         )
    return session.exec(stmt).all()


# --- 3. AÑADE ESTAS DOS NUEVAS FUNCIONES ---

def get_certificate_by_id(certificate_id: int, session: Session) -> UserCertificate:
    """
    Busca un certificado por su ID de tabla.
    """
    certificate = session.get(UserCertificate, certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    # (Aquí podrías añadir lógica para ver si el usuario tiene permiso,
    # pero por ahora lo dejamos simple)
    return certificate


def get_download_url_for_certificate(certificate_id: int, session: Session) -> dict:
    """
    Genera un enlace de descarga (URL con SAS) válido por 1 hora.
    """
    if not blob_service_client or not ACCOUNT_NAME:
        raise HTTPException(status_code=500, detail="Servicio de almacenamiento no configurado.")

    # 1. Buscar la metadata del archivo en SQL
    db_certificate = get_certificate_by_id(certificate_id, session)
    
    # 2. Generar el token SAS
    sas_token = generate_blob_sas(
        account_name=ACCOUNT_NAME,
        container_name=CONTAINER_NAME,
        blob_name=db_certificate.storage_path, # El nombre único (ej. user_3_...pdf)
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1) # Válido por 1 hora
    )
    
    # 3. Construir la URL completa
    download_url = (
        f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
        f"{CONTAINER_NAME}/{db_certificate.storage_path}?{sas_token}"
    )
    
    return {"download_url": download_url}


# --- MODIFICACIÓN 2: Añade esta NUEVA función al final ---
def deactivate_certificate(certificate_id: int, session: Session):
    """
    Desactiva un certificado (soft delete).
    """
    # get_certificate_by_id ya maneja el 404 si no lo encuentra
    db_certificate = get_certificate_by_id(certificate_id, session)

    # (Aquí podrías añadir lógica de permisos, ej. verificar que el user_id
    # que hace la petición es el dueño del db_certificate.user_id)
    
    db_certificate.is_active = 0
    session.add(db_certificate)
    session.commit()
    session.refresh(db_certificate)
    
    # No necesitamos devolver nada, un 204 (No Content) es suficiente
    return

# --- SERVICIO ADICIONAL: Subida de Avatares ---
def upload_avatar_to_blob(user_id: int, file: UploadFile, session: Session) -> str:
    """
    Sube un avatar a Azure Blob Storage y actualiza el perfil del usuario.
    Devuelve la URL pública del avatar.
    """
    if not blob_service_client or not ACCOUNT_NAME:
        raise HTTPException(status_code=500, detail="Servicio de almacenamiento no configurado.")

    # El nombre del nuevo contenedor que creaste
    AVATAR_CONTAINER_NAME = "baristapp-imagenes"

    # 1. Generar un nombre único (ej: user_3_...uuid....jpg)
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"user_{user_id}_{uuid.uuid4()}{file_extension}"



    try:
        # 2. Subir el archivo al contenedor de avatares
        blob_client = blob_service_client.get_blob_client(
            container=AVATAR_CONTAINER_NAME, 
            blob=unique_filename
        )
        
        # Validar tipo de imagen (opcional pero recomendado)
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
             raise HTTPException(status_code=400, detail="Formato de imagen no válido. Usar JPG o PNG.")

        blob_client.upload_blob(file.file, blob_type="BlockBlob")

        # 3. Construir la URL pública (es simple porque el contenedor es público)
        public_url = (
            f"https://{ACCOUNT_NAME}.blob.core.windows.net/"
            f"{AVATAR_CONTAINER_NAME}/{unique_filename}"
        )

        # 4. Actualizar la columna 'avatar_url' en la tabla 'app_user_profile'
        
        # (Aquí podrías tener un problema de importación circular si profile_service
        # importa este archivo. Si eso pasa, movemos esta lógica al controlador)
        
        profile = profile_service.get_profile_by_user_id(user_id, session)
        if profile is None:
            # Si no tiene perfil, lo creamos
            profile = profile_service.upsert_profile(
                user_id=user_id,
                data=profile_service.ProfileUpdate(avatar_url=public_url), # Asumiendo que ProfileUpdate está disponible
                session=session
            )
        else:
            # Si ya tiene perfil, solo actualizamos el campo
            profile.avatar_url = public_url
            session.add(profile)
            session.commit()
            session.refresh(profile)

        return public_url

    except Exception as e:
        # Si algo falla, borrar el blob subido (rollback)
        try:
            blob_client.delete_blob()
        except:
            pass # Ignorar si falla el borrado
        
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error en la subida del avatar: {str(e)}")