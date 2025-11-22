from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import date

from app.services.db.sql_server_connection import get_session
from app.services.db.job_offer_service import JobOfferService
from app.schemas.job_offer import (
    JobOfferCreate,
    JobOfferUpdate,
    JobOfferResponse,
    JobOfferWithApplications
)
from app.services.db.matching_service import MatchingService
from app.schemas.matching import MatchingWorkerResult
from app.schemas.job_application import JobApplicationResponse


router = APIRouter(prefix="/job-offers", tags=["Job Offers"])


@router.post("", response_model=JobOfferResponse, status_code=status.HTTP_201_CREATED)
def create_job_offer(
    job_offer: JobOfferCreate,
    user_id: int = Query(..., description="ID del usuario que crea la oferta (cliente)"),
    session: Session = Depends(get_session)
):
    """
    Crear una nueva oferta de trabajo.

    Soporta campos gig:
    - required_skills
    - urgency
    - date_start / date_end
    - status
    - vacancies_total (si lo incluiste en schema)
    """
    try:
        new_offer = JobOfferService.create_job_offer(session, job_offer, user_id)
        return new_offer
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear oferta de trabajo: {str(e)}"
        )


@router.get("", response_model=List[JobOfferResponse])
def get_all_job_offers(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),

    # filtros base
    is_active: Optional[int] = Query(None, ge=0, le=1, description="Filtrar por estado activo"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrar por estado (PUBLICADO, CERRADO, PAUSADO)"),
    urgency_filter: Optional[str] = Query(None, alias="urgency", description="Filtrar por urgencia (NORMAL/URGENT)"),

    # filtros avanzados
    region: Optional[str] = Query(None, description="Región donde se oferta el turno"),
    comuna: Optional[str] = Query(None, description="Comuna para filtrar"),
    skill: Optional[str] = Query(None, description="Skill requerida (espresso, latte art, etc.)"),
    job_type: Optional[str] = Query(None, description="Tipo de jornada (FULL_TIME, PART_TIME, etc.)"),
    created_by: Optional[int] = Query(None, description="User ID que creó la oferta"),

    min_salary: Optional[float] = Query(None, description="Salario mínimo"),
    max_salary: Optional[float] = Query(None, description="Salario máximo"),

    date_from: Optional[date] = Query(None, description="Fecha mínima del turno"),
    date_to: Optional[date] = Query(None, description="Fecha máxima del turno"),

    session: Session = Depends(get_session)
):
    """
    Obtener todas las ofertas con paginación y filtros avanzados del marketplace.
    Todos los filtros son opcionales y combinables.
    """
    try:
        offers = JobOfferService.get_all_job_offers(
            session=session,
            skip=skip,
            limit=limit,
            is_active=is_active,

            # filtros base
            status=status_filter,
            urgency=urgency_filter,

            # avanzados
            region=region,
            comuna=comuna,
            skill=skill,
            job_type=job_type,
            created_by=created_by,

            min_salary=min_salary,
            max_salary=max_salary,

            date_from=date_from,
            date_to=date_to
        )
        return offers

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ofertas: {str(e)}"
        )


@router.get("/search", response_model=List[JobOfferResponse])
def search_job_offers(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    Buscar ofertas por título, empresa, ubicación, descripción y required_skills.
    """
    try:
        offers = JobOfferService.search_job_offers(session, q, skip, limit)
        return offers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar ofertas: {str(e)}"
        )


@router.get("/by-date", response_model=List[JobOfferResponse])
def get_job_offers_by_date(
    start_date: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    session: Session = Depends(get_session)
):
    """
    Buscar ofertas activas por rango de fechas de creación.
    """
    try:
        offers = JobOfferService.get_job_offers_by_date_range(
            session, start_date, end_date, skip, limit
        )
        return offers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar ofertas por fecha: {str(e)}"
        )


@router.get("/{job_offer_id}", response_model=JobOfferWithApplications)
def get_job_offer(
    job_offer_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener una oferta por ID, incluyendo conteo de postulaciones.
    """
    try:
        offer = JobOfferService.get_job_offer_by_id(session, job_offer_id)
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta de trabajo no encontrada"
            )

        applications_count = JobOfferService.get_applications_count(session, job_offer_id)

        return {
            **offer.model_dump(),
            "applications_count": applications_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener oferta: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[JobOfferResponse])
def get_job_offers_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    Obtener todas las ofertas creadas por un usuario.
    """
    try:
        offers = JobOfferService.get_job_offers_by_user(session, user_id, skip, limit)
        return offers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ofertas del usuario: {str(e)}"
        )


@router.put("/{job_offer_id}", response_model=JobOfferResponse)
def update_job_offer(
    job_offer_id: int,
    job_offer_data: JobOfferUpdate,
    session: Session = Depends(get_session)
):
    """
    Actualizar una oferta (parcial).
    """
    try:
        updated_offer = JobOfferService.update_job_offer(session, job_offer_id, job_offer_data)
        if not updated_offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta de trabajo no encontrada"
            )
        return updated_offer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar oferta: {str(e)}"
        )


@router.delete("/{job_offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_offer(
    job_offer_id: int,
    session: Session = Depends(get_session)
):
    """
    Soft delete: marcar oferta como inactiva.
    """
    try:
        success = JobOfferService.delete_job_offer(session, job_offer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta de trabajo no encontrada"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar oferta: {str(e)}"
        )


@router.get("/{job_offer_id}/matching", response_model=List[MatchingWorkerResult])
def get_matching_workers(
    job_offer_id: int,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session)
):
    """
    Devuelve lista ordenada de workers recomendados para esta oferta.
    Score 0-100 con desglose.
    """
    try:
        matches = MatchingService.get_matching_workers_for_offer(
            session=session,
            job_offer_id=job_offer_id,
            limit=limit
        )
        return matches
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando matching: {str(e)}"
        )


@router.post("/{job_offer_id}/select/{application_id}", response_model=JobOfferResponse)
def select_candidate_and_close_offer(
    job_offer_id: int,
    application_id: int,
    recruiter_notes: str | None = Query(None, description="Notas opcionales del reclutador"),
    session: Session = Depends(get_session)
):
    """
    Contrata a un postulante (multi-vacante):
    - Marca HIRED la postulación seleccionada.
    - Incrementa vacancies_filled en la oferta.
    - Mientras queden cupos, la oferta sigue PUBLICADO.
    - Cuando se llena el último cupo, cierra oferta y rechaza el resto.
    """
    try:
        offer = JobOfferService.select_application_and_close_offer(
            session=session,
            job_offer_id=job_offer_id,
            application_id=application_id,
            recruiter_notes=recruiter_notes
        )

        if not offer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo contratar (oferta llena, no existe, o postulación inválida)"
            )

        return offer

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error seleccionando candidato: {str(e)}"
        )


@router.put("/{job_offer_id}/close", response_model=JobOfferResponse)
def close_offer(
    job_offer_id: int,
    session: Session = Depends(get_session)
):
    """
    Cierra la oferta sin contratar a nadie.
    """
    try:
        offer = JobOfferService.close_offer(session, job_offer_id)
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oferta no encontrada"
            )
        return offer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cerrando oferta: {str(e)}"
        )


@router.get("/{job_offer_id}/selected-application", response_model=JobApplicationResponse)
def get_selected_application(
    job_offer_id: int,
    session: Session = Depends(get_session)
):
    """
    Devuelve la primera postulación seleccionada como ganadora (si existe).
    """
    try:
        app_selected = JobOfferService.get_selected_application(session, job_offer_id)
        if not app_selected:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay postulación seleccionada para esta oferta"
            )
        return app_selected
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo seleccionado: {str(e)}"
        )
