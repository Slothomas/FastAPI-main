# app/controllers/job_offer_controller.py
import traceback
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.services.db.sql_server_connection import get_session
from app.services.db.job_offer_service import JobOfferService
from app.services.db.matching_service import MatchingService

from app.schemas.job_offer import (
    JobOfferCreate,
    JobOfferUpdate,
    JobOfferResponse,
    JobOfferWithApplications,
)
from app.schemas.matching import MatchingWorkerResult
from app.schemas.job_application import JobApplicationResponse

router = APIRouter(prefix="/job-offers", tags=["Job Offers"])


# ============================================================
# CREATE (multi-local ready)
# ============================================================
@router.post("/", response_model=JobOfferResponse, status_code=status.HTTP_201_CREATED)
def create_job_offer(
    job_offer: JobOfferCreate,
    user_id: int = Query(..., description="ID del usuario que crea la oferta (cliente)"),
    session: Session = Depends(get_session),
):
    """
    Crear una nueva oferta de trabajo.

    ✅ Soporta multi-local si el payload incluye business_location_id:
    - valida propietario del negocio/local
    - autopuebla company/location/region/comuna
    """
    try:
        new_offer = JobOfferService.create_job_offer(session, job_offer, user_id)
        return new_offer

    except ValueError as ve:
        # errores de validación multi-local
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear oferta de trabajo: {str(e)}",
        )


# ============================================================
# GET ALL (Marketplace) — BLINDADO CON JSONResponse
# ============================================================
@router.get("/")
def get_all_job_offers(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    # filtros base
    is_active: Optional[int] = Query(None, ge=0, le=1, description="Filtrar por estado activo"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrar por estado"),
    urgency_filter: Optional[str] = Query(None, alias="urgency", description="Filtrar por urgencia"),
    # filtros avanzados
    region: Optional[str] = Query(None, description="Región"),
    comuna: Optional[str] = Query(None, description="Comuna"),
    skill: Optional[str] = Query(None, description="Skill requerida"),
    job_type: Optional[str] = Query(None, description="Tipo de jornada"),
    created_by: Optional[int] = Query(None, description="User ID"),
    min_salary: Optional[float] = Query(None, description="Salario mínimo"),
    max_salary: Optional[float] = Query(None, description="Salario máximo"),
    date_from: Optional[date] = Query(None, description="Fecha mínima"),
    date_to: Optional[date] = Query(None, description="Fecha máxima"),
    session: Session = Depends(get_session),
):
    """
    Obtener todas las ofertas. Usa JSONResponse directo para evitar errores de validación de Enums.
    """
    try:
        offers = JobOfferService.get_all_job_offers(
            session=session,
            skip=skip,
            limit=limit,
            is_active=is_active,
            status=status_filter,
            urgency=urgency_filter,
            region=region,
            comuna=comuna,
            skill=skill,
            job_type=job_type,
            created_by=created_by,
            min_salary=min_salary,
            max_salary=max_salary,
            date_from=date_from,
            date_to=date_to,
        )

        result = []
        for o in offers:
            try:
                safe_job_type = o.job_type.value if hasattr(o.job_type, "value") else str(o.job_type)
                safe_urgency = o.urgency.value if hasattr(o.urgency, "value") else str(o.urgency)
                safe_status = o.status.value if hasattr(o.status, "value") else str(o.status)

                result.append(
                    {
                        "id": o.id,
                        "title": o.title,
                        "company": o.company,
                        "location": o.location,
                        "job_type": safe_job_type,
                        "description": o.description,
                        "salary_range": o.salary_range,
                        "requirements": o.requirements,
                        "required_skills": o.required_skills,
                        "urgency": safe_urgency,
                        "status": safe_status,
                        "region": o.region,
                        "comuna": o.comuna,
                        "date_start": o.date_start.isoformat() if o.date_start else None,
                        "date_end": o.date_end.isoformat() if o.date_end else None,
                        "created_by": o.created_by,
                        "selected_application_id": o.selected_application_id,
                        "filled_at": o.filled_at.isoformat() if o.filled_at else None,
                        "vacancies_filled": getattr(o, "vacancies_filled", 0) or 0,
                        "vacancies_total": getattr(o, "vacancies_total", 1) or 1,
                        "is_active": o.is_active,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
                        "business_id": getattr(o, "business_id", None),
                        "location_id": getattr(o, "location_id", None),
                    }
                )
            except Exception as row_error:
                print(f"⚠️ Error serializando oferta ID {getattr(o, 'id', '?')}: {row_error}")
                continue

        return JSONResponse(content=jsonable_encoder(result))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ofertas: {str(e)}",
        )


# ============================================================
# SEARCH
# ============================================================
@router.get("/search", response_model=List[JobOfferResponse])
def search_job_offers(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    try:
        offers = JobOfferService.search_job_offers(session, q, skip, limit)
        return offers
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar ofertas: {str(e)}",
        )


# ============================================================
# BY DATE RANGE
# ============================================================
@router.get("/by-date", response_model=List[JobOfferResponse])
def get_job_offers_by_date(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    try:
        offers = JobOfferService.get_job_offers_by_date_range(
            session, start_date, end_date, skip, limit
        )
        return offers
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar ofertas por fecha: {str(e)}",
        )


# ============================================================
# GET BY ID
# ============================================================
@router.get("/{job_offer_id}", response_model=JobOfferWithApplications)
def get_job_offer(
    job_offer_id: int,
    session: Session = Depends(get_session),
):
    try:
        offer = JobOfferService.get_job_offer_by_id(session, job_offer_id)
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta de trabajo no encontrada",
            )

        applications_count = JobOfferService.get_applications_count(session, job_offer_id)

        return {
            **offer.model_dump(),
            "applications_count": applications_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener oferta: {str(e)}",
        )


# ============================================================
# BY USER
# ============================================================
@router.get("/user/{user_id}", response_model=List[JobOfferResponse])
def get_job_offers_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session),
):
    try:
        offers = JobOfferService.get_job_offers_by_user(session, user_id, skip, limit)
        return offers
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ofertas del usuario: {str(e)}",
        )


# ============================================================
# UPDATE
# ============================================================
@router.put("/{job_offer_id}", response_model=JobOfferResponse)
def update_job_offer(
    job_offer_id: int,
    job_offer_data: JobOfferUpdate,
    session: Session = Depends(get_session),
):
    try:
        updated_offer = JobOfferService.update_job_offer(session, job_offer_id, job_offer_data)
        if not updated_offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta de trabajo no encontrada",
            )
        return updated_offer
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar oferta: {str(e)}",
        )


# ============================================================
# DELETE
# ============================================================
@router.delete("/{job_offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_offer(
    job_offer_id: int,
    session: Session = Depends(get_session),
):
    try:
        success = JobOfferService.delete_job_offer(session, job_offer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta de trabajo no encontrada",
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar oferta: {str(e)}",
        )


# ============================================================
# MATCHING
# ============================================================
@router.get("/{job_offer_id}/matching", response_model=List[MatchingWorkerResult])
def get_matching_workers(
    job_offer_id: int,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    try:
        matches = MatchingService.get_matching_workers_for_offer(
            session=session,
            job_offer_id=job_offer_id,
            limit=limit,
        )
        return matches
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando matching: {str(e)}",
        )


# ============================================================
# SELECT CANDIDATE
# ============================================================
@router.post("/{job_offer_id}/select/{application_id}")
def select_candidate(
    job_offer_id: int,
    application_id: int,
    recruiter_notes: str | None = Query(None),
    session: Session = Depends(get_session),
):
    try:
        offer = JobOfferService.select_application_and_close_offer(
            session=session,
            job_offer_id=job_offer_id,
            application_id=application_id,
            recruiter_notes=recruiter_notes,
        )

        if not offer:
            raise HTTPException(
                status_code=400,
                detail="No se pudo seleccionar candidato",
            )

        data = offer.model_dump()

        # enums -> valores
        for key in ["status", "job_type", "urgency"]:
            v = data.get(key)
            data[key] = v.value if hasattr(v, "value") else v

        # null-safety
        data["vacancies_filled"] = data.get("vacancies_filled") or 0
        data["vacancies_total"] = data.get("vacancies_total") or 1
        data["is_active"] = data.get("is_active") if data.get("is_active") is not None else 1

        # NUEVO: IDs de negocio y local
        data["business_id"] = data.get("business_id") or getattr(offer, "business_id", None)
        data["location_id"] = data.get("location_id") or getattr(offer, "location_id", None)

        return JSONResponse(content=jsonable_encoder(data))

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error seleccionando candidato: {str(e)}",
        )


# ============================================================
# CLOSE OFFER
# ============================================================
@router.put("/{job_offer_id}/close", response_model=JobOfferResponse)
def close_offer(
    job_offer_id: int,
    session: Session = Depends(get_session),
):
    try:
        offer = JobOfferService.close_offer(session, job_offer_id)
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta no encontrada",
            )
        return offer
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cerrando oferta: {str(e)}",
        )


# ============================================================
# SELECTED APPLICATION
# ============================================================
@router.get("/{job_offer_id}/selected-application", response_model=JobApplicationResponse)
def get_selected_application(
    job_offer_id: int,
    session: Session = Depends(get_session),
):
    try:
        app_selected = JobOfferService.get_selected_application(session, job_offer_id)
        if not app_selected:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay postulación seleccionada para esta oferta",
            )
        return app_selected
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo seleccionado: {str(e)}",
        )
