from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.services.db.assignment_service import AssignmentService
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
)
from app.services.db.sql_server_connection import get_session

# Enum de estado de asignación
from app.models.job_assignment import AssignmentStatus

# servicio que genera el GigPayment
from app.services.db.gig_payments import create_gig_payment_from_assignment

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("/", response_model=AssignmentResponse)
def assign_worker(
    data: AssignmentCreate,
    session: Session = Depends(get_session),
):
    assignment = AssignmentService.assign_worker(
        session=session,
        job_offer_id=data.job_offer_id,
        worker_id=data.worker_id,
        client_id=data.client_id,
    )
    if not assignment:
        raise HTTPException(404, "No se pudo asignar turno")
    return assignment


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    session: Session = Depends(get_session),
):
    # 1) Actualizamos el estado de la asignación
    assignment = AssignmentService.update_assignment_status(
        session, assignment_id, data.status
    )
    if not assignment:
        raise HTTPException(404, "Asignación no encontrada")

    # 2) Normalizamos el estado para soportar Enum o string
    try:
        # Si es Enum, .value suele ser "COMPLETED", "COMPLETED_CONFIRMED", etc.
        status_value = assignment.status.value  # type: ignore[attr-defined]
    except AttributeError:
        # Si ya viene como string desde la BD
        status_value = str(assignment.status)

    status_value = status_value.strip().upper()

    # 🧠 Regla de negocio:
    # Si la asignación queda en estado COMPLETED o COMPLETED_CONFIRMED,
    # generamos (si no existe) el GigPayment asociado.
    if status_value in ("COMPLETED", "COMPLETED_CONFIRMED"):
        create_gig_payment_from_assignment(session, assignment)

    return assignment


@router.get("/worker/{worker_id}", response_model=list[AssignmentResponse])
def list_for_worker(
    worker_id: int,
    session: Session = Depends(get_session),
):
    return AssignmentService.get_assignments_for_worker(session, worker_id)


@router.get("/client/{client_id}", response_model=list[AssignmentResponse])
def list_for_client(
    client_id: int,
    session: Session = Depends(get_session),
):
    return AssignmentService.get_assignments_for_client(session, client_id)
