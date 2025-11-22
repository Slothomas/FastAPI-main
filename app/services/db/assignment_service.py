from datetime import datetime
from sqlmodel import Session, select

from app.models.job_assignment import JobAssignment, AssignmentStatus
from app.models.job_offer import JobOffer
from app.models.user import AppUser  # <- tu usuario real


class AssignmentService:

    @staticmethod
    def assign_worker(session: Session, job_offer_id: int, worker_id: int, client_id: int):
        """
        Crea una asignación de turno entre un trabajador (AppUser) y una oferta.
        """

        # 1) Validar oferta
        job_offer = session.get(JobOffer, job_offer_id)
        if not job_offer:
            raise ValueError(f"JobOffer {job_offer_id} no existe")

        if job_offer.is_active == 0:
            raise ValueError("La oferta está inactiva y no puede asignarse")

        # 2) Validar que el trabajador exista como AppUser
        worker = session.get(AppUser, worker_id)
        if not worker:
            raise ValueError(f"Worker (AppUser) con id {worker_id} no existe")

        # 3) Validar que el cliente exista
        client = session.get(AppUser, client_id)
        if not client:
            raise ValueError(f"Client (AppUser) con id {client_id} no existe")

        # 4) Crear asignación
        assignment = JobAssignment(
            job_offer_id=job_offer_id,
            worker_id=worker_id,
            client_id=client_id,
            status=AssignmentStatus.ASSIGNED
,   # MINÚSCULA (según enum)
            assigned_at=datetime.utcnow(),
            notes="Asignado automáticamente"
        )

        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        return assignment

    @staticmethod
    def update_assignment_status(session: Session, assignment_id: int, status: AssignmentStatus):
        assignment = session.get(JobAssignment, assignment_id)
        if not assignment:
            return None

        assignment.status = status

        if status == AssignmentStatus.COMPLETED:
            assignment.completed_at = datetime.utcnow()

        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        return assignment

    @staticmethod
    def get_assignments_for_worker(session: Session, worker_id: int):
        q = select(JobAssignment).where(JobAssignment.worker_id == worker_id)
        return list(session.exec(q).all())

    @staticmethod
    def get_assignments_for_client(session: Session, client_id: int):
        q = select(JobAssignment).where(JobAssignment.client_id == client_id)
        return list(session.exec(q).all())
