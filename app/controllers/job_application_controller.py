import traceback
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select

from app.services.db.sql_server_connection import get_session
from app.services.db.job_application_service import JobApplicationService
from app.services.db.assignment_service import AssignmentService
from app.services.db.gig_payments import create_gig_payment_from_assignment

from app.models.job_application import JobApplication, ApplicationStatus
from app.models.gig_payment import GigPayment

from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationUpdateStatus,
    JobApplicationResponse,
    JobApplicationWithUser,
    JobApplicationWithOffer,
)
from app.schemas.job_application_bulk import (
    BulkStatusUpdate,
    JobOfferBulkUpdate,
    BulkUpdateResponse,
)

router = APIRouter(prefix="/job-applications", tags=["Job Applications"])


@router.post("/", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job_application(
    application: JobApplicationCreate,
    user_id: int = Query(..., description="ID del usuario que postula"),
    session: Session = Depends(get_session),
):
    try:
        new_application = JobApplicationService.create_application(session, application, user_id)
        if not new_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear la postulación. La oferta no existe, está inactiva, o ya has postulado anteriormente.",
            )
        return new_application
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear postulación: {str(e)}",
        )


@router.get("/user/{user_id}", response_model=List[JobApplicationWithOffer])
def get_my_applications(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    try:
        applications = JobApplicationService.get_applications_by_user_with_offer(
            session, user_id, skip, limit
        )
        return applications
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulaciones: {str(e)}",
        )


@router.get("/job-offer/{job_offer_id}", response_model=List[JobApplicationResponse])
def get_applications_for_job_offer(
    job_offer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    try:
        applications = JobApplicationService.get_applications_by_job_offer(
            session, job_offer_id, skip, limit
        )
        return applications
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulaciones: {str(e)}",
        )


@router.get("/{application_id}", response_model=JobApplicationResponse)
def get_application(
    application_id: int,
    session: Session = Depends(get_session),
):
    try:
        application = JobApplicationService.get_application_by_id(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada"
            )
        return application
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulación: {str(e)}",
        )


@router.get("/{application_id}/with-user", response_model=JobApplicationWithUser)
def get_application_with_user(
    application_id: int,
    session: Session = Depends(get_session),
):
    try:
        application = JobApplicationService.get_application_with_user_info(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada"
            )
        return application
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulación: {str(e)}",
        )


@router.get("/{application_id}/with-offer", response_model=JobApplicationWithOffer)
def get_application_with_offer(
    application_id: int,
    session: Session = Depends(get_session),
):
    try:
        application = JobApplicationService.get_application_with_offer_info(session, application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Postulación no encontrada"
            )
        return application
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener postulación: {str(e)}",
        )


# ============================================================================
# UPDATE STATUS (BLINDADO - SIN response_model PARA EVITAR 422)
# ============================================================================
@router.put("/{application_id}/status")
def update_application_status(
    application_id: int,
    payload: dict = Body(...),
    session: Session = Depends(get_session),
):
    """
    Actualizar estado de una postulación y sincronizar vacantes
    (HIRED -> REJECTED = libera cupo).
    + Si rejected, guarda rejection_reason / rejection_note
    """

    print(f"\n🔵 [DEBUG] UPDATE STATUS controller para {application_id}, payload={payload}")

    new_status_raw = payload.get("status")
    recruiter_notes = payload.get("recruiter_notes")

    # nuevos campos
    rejection_reason = payload.get("rejection_reason")
    rejection_note = payload.get("rejection_note")

    if not new_status_raw:
        raise HTTPException(status_code=400, detail="Falta 'status' en payload")

    new_status_norm = str(new_status_raw).strip().lower()

    status_data = JobApplicationUpdateStatus(
        status=new_status_norm,
        recruiter_notes=recruiter_notes,
        rejection_reason=rejection_reason,
        rejection_note=rejection_note,
    )

    updated = JobApplicationService.update_application_status(
        session, application_id, status_data
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    safe_status = (
        str(updated.status.value)
        if hasattr(updated.status, "value")
        else str(updated.status)
    )

    return JSONResponse(
        content={
          "id": updated.id,
          "status": safe_status,
          "message": "Estado actualizado correctamente (vacantes sincronizadas)",
          "recruiter_notes": updated.recruiter_notes,
          "rejection_reason": updated.rejection_reason,
          "rejection_note": updated.rejection_note,
          "rejected_at": updated.rejected_at.isoformat()
          if updated.rejected_at
          else None,
        }
    )


# ========== ENDPOINTS PARA ACTUALIZACIÓN EN LOTE ==========

@router.put("/bulk/update-status")
def bulk_update_application_status(
    bulk_data: BulkStatusUpdate,
    session: Session = Depends(get_session),
):
    try:
        updated_ids = JobApplicationService.bulk_update_status(
            session,
            bulk_data.application_ids,
            bulk_data.status,
            bulk_data.recruiter_notes,
        )

        return JSONResponse(
            content={
                "updated_count": len(updated_ids),
                "application_ids": updated_ids,
                "status": str(bulk_data.status),
            }
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar postulaciones en lote: {str(e)}",
        )


@router.put("/bulk/job-offer/{job_offer_id}")
def bulk_update_by_job_offer(
    job_offer_id: int,
    bulk_data: JobOfferBulkUpdate,
    session: Session = Depends(get_session),
):
    try:
        if bulk_data.job_offer_id != job_offer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El job_offer_id en la URL no coincide con el del body",
            )

        updated_ids = JobApplicationService.bulk_update_by_job_offer(
            session,
            job_offer_id,
            bulk_data.status,
            bulk_data.exclude_ids,
            bulk_data.recruiter_notes,
        )

        return JSONResponse(
            content={
                "updated_count": len(updated_ids),
                "application_ids": updated_ids,
                "status": str(bulk_data.status),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar postulaciones: {str(e)}",
        )


# ============================================================================
# COMPLETE JOB (uno marca, otro confirma)
# ============================================================================
@router.post("/{application_id}/complete")
def mark_or_confirm_completed(
    application_id: int,
    actor_user_id: int = Query(..., description="ID del usuario que ejecuta la acción"),
    actor_role: str = Query(..., description="Rol del actor: employer | worker"),
    session: Session = Depends(get_session),
):
    """
    Flujo post-trabajo:

    1) Si status = hired:
       - worker marca -> completed_by_worker
       - employer marca -> completed_by_employer

    2) Si status = completed_by_worker:
       - employer confirma -> completed_confirmed

    3) Si status = completed_by_employer:
       - worker confirma -> completed_confirmed

    4) Si status = completed_confirmed:
       - idempotente, no cambia (pero no rompe)

    NOTA:
    Los flags worker_reviewed / employer_reviewed NO se tocan aquí.
    Se actualizan solo al crear una review.
    """

    actor_role_norm = str(actor_role).strip().lower()
    if actor_role_norm not in ("employer", "worker"):
        raise HTTPException(status_code=400, detail="actor_role debe ser 'employer' o 'worker'")

    updated = JobApplicationService.complete_application(
        session=session,
        application_id=application_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role_norm,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")

    # Status en string plano
    safe_status = (
        str(updated.status.value)
        if hasattr(updated.status, "value")
        else str(updated.status)
    )

    # =====================================================
    # 🔥 NUEVO: si la postulación quedó COMPLETED_CONFIRMED,
    # generamos (si no existe) el GigPayment asociado
    # =====================================================
    if safe_status == "completed_confirmed":
        try:
            # 1) obtener las asignaciones del barista
            worker_assignments = AssignmentService.get_assignments_for_worker(
                session, updated.user_id
            )

            # 2) buscar la que corresponde a esta oferta
            assignment = next(
                (a for a in worker_assignments if a.job_offer_id == updated.job_offer_id),
                None,
            )

            if assignment:
                # 3) evitar duplicados: ¿ya existe GigPayment para este assignment?
                existing_payment = session.exec(
                    select(GigPayment).where(GigPayment.assignment_id == assignment.id)
                ).first()

                if not existing_payment:
                    create_gig_payment_from_assignment(session, assignment)
        except Exception as e:
            # No rompemos el flujo de completado si el pago falla,
            # pero dejamos trazabilidad en logs
            traceback.print_exc()
            print(f"[WARN] Error generando GigPayment para application {application_id}: {e}")

    return JSONResponse(
        content={
            "id": updated.id,
            "status": safe_status,
            "message": "Estado de completado actualizado correctamente",
        }
    )


@router.put("/{application_id}/refresh-matching", response_model=JobApplicationResponse)
def refresh_application_matching(
    application_id: int,
    session: Session = Depends(get_session),
):
    try:
        app_updated = JobApplicationService.refresh_matching_score(session, application_id)
        if not app_updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Postulación no encontrada",
            )
        return JobApplicationResponse.from_model(app_updated)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refrescando matching: {str(e)}",
        )
