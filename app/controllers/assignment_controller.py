from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.services.db.assignment_service import AssignmentService
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
)
from app.services.db.sql_server_connection import get_session

# 👇 nuevo import: servicio que genera el GigPayment
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
    # Actualizamos el estado de la asignación
    assignment = AssignmentService.update_assignment_status(
        session, assignment_id, data.status
    )
    if not assignment:
        raise HTTPException(404, "Asignación no encontrada")

    # 🧠 Regla de negocio:
    # Si la asignación queda en estado COMPLETED,
    # generamos (si no existe) el GigPayment asociado.
    status_str = str(assignment.status).upper()
    if status_str == "COMPLETED":
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
