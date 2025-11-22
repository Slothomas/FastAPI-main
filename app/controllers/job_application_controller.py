from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List

from app.services.db.sql_server_connection import get_session
from app.services.db.job_application_service import JobApplicationService
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationUpdateStatus,
    JobApplicationResponse,
    JobApplicationWithUser,
    JobApplicationWithOffer
)
from app.schemas.job_application_bulk import (
    BulkStatusUpdate,
    JobOfferBulkUpdate,
    BulkUpdateResponse
)

router = APIRouter(prefix="/job-applications", tags=["Job Applications"])


@router.post("/", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job_application(
    application: JobApplicationCreate,
    user_id: int = Query(..., description="ID del usuario que postula"),
    session: Session = Depends(get_session)
):
    """
    Crear una nueva postulación a una oferta de trabajo.

    - **job_offer_id**: ID de la oferta de trabajo
    - **cover_letter**: Carta de presentación (opcional)

    El usuario debe tener un CV completado para postular.
    No se puede postular dos veces a la misma oferta.
    """
    try:
        new_application = JobApplicationService.create_application(session, application, user_id)
        if not new_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear la postulación. La oferta no existe, está inactiva, o ya has postulado anteriormente."
            )
        return new_application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear postulación: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[JobApplicationWithOffer])
def get_my_applications(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    Obtener todas las postulaciones de un usuario con información de las ofertas.

    Devuelve cada postulación con:
    - ID de la postulación
    - Estado (pending, under_review, interview_scheduled, interviewed, offered, hired, rejected)
    - Carta de presentación
    - Título de la oferta de trabajo
    - Empresa
    - Ubicación
    - Fecha de postulación

    Ideal para que el usuario vea todas sus postulaciones y el estado de cada una.
    """
    try:
        applications = JobApplicationService.get_applications_by_user_with_offer(
            session, user_id, skip, limit
        )
        return applications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulaciones: {str(e)}"
        )


@router.get("/job-offer/{job_offer_id}", response_model=List[JobApplicationResponse])
def get_applications_for_job_offer(
    job_offer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    Obtener todas las postulaciones para una oferta de trabajo específica.
    Útil para reclutadores que quieren ver quién ha aplicado.
    """
    try:
        applications = JobApplicationService.get_applications_by_job_offer(
            session, job_offer_id, skip, limit
        )
        return applications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulaciones: {str(e)}"
        )


@router.get("/{application_id}", response_model=JobApplicationResponse)
def get_application(
    application_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener una postulación específica por ID.
    """
    try:
        application = JobApplicationService.get_application_by_id(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada"
            )
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulación: {str(e)}"
        )


@router.get("/{application_id}/with-user", response_model=JobApplicationWithUser)
def get_application_with_user(
    application_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener una postulación con información del usuario que aplicó.
    Útil para reclutadores.
    """
    try:
        application = JobApplicationService.get_application_with_user_info(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada"
            )
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulación: {str(e)}"
        )


@router.get("/{application_id}/with-offer", response_model=JobApplicationWithOffer)
def get_application_with_offer(
    application_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener una postulación con información de la oferta de trabajo.
    Útil para usuarios que quieren ver detalles de su postulación.
    """
    try:
        application = JobApplicationService.get_application_with_offer_info(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada"
            )
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulación: {str(e)}"
        )


@router.put("/{application_id}/status", response_model=JobApplicationResponse)
def update_application_status(
    application_id: int,
    status_data: JobApplicationUpdateStatus,
    session: Session = Depends(get_session)
):
    """
    Actualizar el estado de una postulación.
    Solo debe ser usado por reclutadores.

    El campo **status** ahora es validado por Enum (ApplicationStatus) en el schema,
    por lo que no se valida manualmente aquí.
    """
    try:
        updated_application = JobApplicationService.update_application_status(
            session, application_id, status_data
        )
        if not updated_application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada"
            )
        return updated_application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar estado: {str(e)}"
        )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    user_id: int = Query(..., description="ID del usuario que elimina"),
    session: Session = Depends(get_session)
):
    """
    Eliminar una postulación.
    Solo el usuario que creó la postulación puede eliminarla.
    """
    try:
        success = JobApplicationService.delete_application(session, application_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada o no tienes permiso para eliminarla"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar postulación: {str(e)}"
        )


# ========== ENDPOINTS PARA ACTUALIZACIÓN EN LOTE ==========

@router.put("/bulk/update-status", response_model=BulkUpdateResponse)
def bulk_update_application_status(
    bulk_data: BulkStatusUpdate,
    session: Session = Depends(get_session)
):
    """
    Actualizar el estado de múltiples postulaciones a la vez.

    **Caso de uso:** El reclutador revisó 20 CVs y quiere marcar todos como "under_review"

    **Ejemplo:**
    ```json
    {
      "application_ids": [1, 2, 3, 4, 5],
      "status": "under_review",
      "recruiter_notes": "Primeros 5 candidatos seleccionados para revisión"
    }
    ```
    """
    try:
        updated_ids = JobApplicationService.bulk_update_status(
            session,
            bulk_data.application_ids,
            bulk_data.status,
            bulk_data.recruiter_notes
        )

        return BulkUpdateResponse(
            updated_count=len(updated_ids),
            application_ids=updated_ids,
            status=bulk_data.status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar postulaciones en lote: {str(e)}"
        )


@router.put("/bulk/job-offer/{job_offer_id}", response_model=BulkUpdateResponse)
def bulk_update_by_job_offer(
    job_offer_id: int,
    bulk_data: JobOfferBulkUpdate,
    session: Session = Depends(get_session)
):
    """
    Actualizar todas las postulaciones de una oferta, excluyendo algunas.

    **Caso de uso:** El reclutador encontró al candidato ideal (ID: 15) y quiere
    rechazar automáticamente a todos los demás postulantes.

    **Ejemplo 1 - Rechazar todos excepto los seleccionados:**
    ```json
    {
      "job_offer_id": 10,
      "exclude_ids": [15, 20],
      "status": "rejected",
      "recruiter_notes": "Posición cubierta, gracias por postular"
    }
    ```

    **Ejemplo 2 - Poner todos en espera excepto los que ya están en entrevista:**
    ```json
    {
      "job_offer_id": 10,
      "exclude_ids": [15, 20, 25],
      "status": "pending",
      "recruiter_notes": "En lista de espera"
    }
    ```
    """
    try:
        # Validar que el job_offer_id coincida
        if bulk_data.job_offer_id != job_offer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El job_offer_id en la URL no coincide con el del body"
            )

        updated_ids = JobApplicationService.bulk_update_by_job_offer(
            session,
            job_offer_id,
            bulk_data.status,
            bulk_data.exclude_ids,
            bulk_data.recruiter_notes
        )

        return BulkUpdateResponse(
            updated_count=len(updated_ids),
            application_ids=updated_ids,
            status=bulk_data.status
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar postulaciones: {str(e)}"
        )


@router.put("/{application_id}/refresh-matching", response_model=JobApplicationResponse)
def refresh_application_matching(
    application_id: int,
    session: Session = Depends(get_session)
):
    """
    Recalcula el matching_score de la postulación.
    """
    try:
        app_updated = JobApplicationService.refresh_matching_score(session, application_id)
        if not app_updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada"
            )
        return JobApplicationResponse.from_model(app_updated)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refrescando matching: {str(e)}"
        )
