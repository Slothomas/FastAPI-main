# app/services/db/job_application_service.py

from datetime import datetime
from typing import List, Optional
import json
from sqlmodel import Session, select
from fastapi import HTTPException

# schemas (solo DTOs)
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationUpdateStatus
)

# models (entidades reales)
from app.models.job_application import (
    JobApplication,
    ApplicationStatus,
    RejectionReason
)

from app.models.job_offer import JobOffer, JobOfferStatus
from app.services.db.matching_service import MatchingService
from app.models.user import AppUser


class JobApplicationService:
    """Servicio para gestionar postulaciones a ofertas de trabajo"""

    # ----------------------------------------------------------------------
    # CREATE
    # ----------------------------------------------------------------------
    @staticmethod
    def create_application(
        session: Session,
        application_data: JobApplicationCreate,
        user_id: int
    ) -> Optional[JobApplication]:
        """Crear una nueva postulación"""

        # Verificar que la oferta existe y está activa
        job_offer = session.get(JobOffer, application_data.job_offer_id)
        if not job_offer or job_offer.is_active == 0:
            return None

        # Verificar que el usuario no haya aplicado ya
        existing = session.exec(
            select(JobApplication).where(
                JobApplication.job_offer_id == application_data.job_offer_id,
                JobApplication.user_id == user_id
            )
        ).first()

        if existing:
            return None  # Ya aplicó anteriormente

        # ===== NUEVO: calcular matching persistido =====
        match = MatchingService.compute_match_for_user(
            session=session,
            job_offer_id=application_data.job_offer_id,
            user_id=user_id
        )
        score = match.get("score", 0.0)
        breakdown = match.get("breakdown", {})

        application = JobApplication(
            job_offer_id=application_data.job_offer_id,
            user_id=user_id,
            cover_letter=application_data.cover_letter,
            status=ApplicationStatus.PENDING,
            recruiter_notes=None,

            # matching persistido
            match_score=score,
            match_breakdown_json=json.dumps(breakdown),
            match_refreshed_at=datetime.now(),

            applied_at=datetime.now(),
            updated_at=datetime.now()
        )

        session.add(application)
        session.commit()
        session.refresh(application)
        return application

    # ----------------------------------------------------------------------
    # REFRESH MATCHING SCORE (PUNTO 6)
    # ----------------------------------------------------------------------
    @staticmethod
    def refresh_matching_score(
        session: Session,
        application_id: int
    ) -> Optional[JobApplication]:
        """
        Recalcula el matching_score para una postulación existente.
        Útil si cambia perfil/CV o requisitos de la oferta.
        """
        application = session.get(JobApplication, application_id)
        if not application:
            return None

        match = MatchingService.compute_match_for_user(
            session=session,
            job_offer_id=application.job_offer_id,
            user_id=application.user_id
        )

        application.match_score = match.get("score", 0.0)
        application.match_breakdown_json = json.dumps(match.get("breakdown", {}))
        application.match_refreshed_at = datetime.now()
        application.updated_at = datetime.now()

        session.add(application)
        session.commit()
        session.refresh(application)
        return application

    # ----------------------------------------------------------------------
    # GET BY ID
    # ----------------------------------------------------------------------
    @staticmethod
    def get_application_by_id(session: Session, application_id: int) -> Optional[JobApplication]:
        """Obtener una postulación por ID"""
        return session.get(JobApplication, application_id)

    # ----------------------------------------------------------------------
    # GET BY USER
    # ----------------------------------------------------------------------
    @staticmethod
    def get_applications_by_user(
        session: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobApplication]:
        """Obtener todas las postulaciones de un usuario"""
        query = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(JobApplication.applied_at.desc())
        )
        return list(session.exec(query).all())

    # ----------------------------------------------------------------------
    # GET BY JOB OFFER
    # ----------------------------------------------------------------------
    @staticmethod
    def get_applications_by_job_offer(
        session: Session,
        job_offer_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobApplication]:
        """Obtener todas las postulaciones de una oferta de trabajo"""
        query = (
            select(JobApplication)
            .where(JobApplication.job_offer_id == job_offer_id)
            .offset(skip)
            .limit(limit)
            .order_by(JobApplication.applied_at.desc())
        )
        return list(session.exec(query).all())

    # ----------------------------------------------------------------------
    # UPDATE STATUS
    # ----------------------------------------------------------------------
    @staticmethod
    def update_application_status(
        session: Session,
        application_id: int,
        status_data: JobApplicationUpdateStatus
    ) -> Optional[JobApplication]:
        """Actualizar el estado de una postulación
        + libera vacante si hired -> rejected
        + guarda motivo/nota si rejected
        """

        application = session.get(JobApplication, application_id)
        if not application:
            return None

        # Normalizar a string lower seguro
        old_status = str(application.status.value if hasattr(application.status, "value") else application.status or "").strip().lower()
        new_status = str(status_data.status or "").strip().lower()

        # Validar que el nuevo estado exista en el Enum
        valid_statuses = {s.value for s in ApplicationStatus}
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail="status inválido")

        # Castear a enum
        application.status = ApplicationStatus(new_status)

        if status_data.recruiter_notes is not None:
            application.recruiter_notes = status_data.recruiter_notes

        # ===== NUEVO: lógica rechazo =====
        if new_status == "rejected":
            if not status_data.rejection_reason:
                raise HTTPException(status_code=400, detail="rejection_reason es obligatorio al rechazar")

            valid_reasons = {r.value for r in RejectionReason}
            if status_data.rejection_reason not in valid_reasons:
                raise HTTPException(status_code=400, detail="rejection_reason inválido")

            application.rejection_reason = status_data.rejection_reason
            application.rejection_note = status_data.rejection_note
            application.rejected_at = datetime.now()

        else:
            # si cambia a otro estado, limpia rechazo
            application.rejection_reason = None
            application.rejection_note = None
            application.rejected_at = None

        application.updated_at = datetime.now()
        session.add(application)

        # 2) traer oferta asociada
        offer = session.get(JobOffer, application.job_offer_id)

        if offer:
            offer.vacancies_filled = offer.vacancies_filled or 0
            offer.vacancies_total = offer.vacancies_total or 1

            # 3) hired -> rejected => restar vacante
            if old_status == "hired" and new_status == "rejected":
                offer.vacancies_filled = max(0, offer.vacancies_filled - 1)

                # si estaba cerrada por cupos, reabrir
                offer_status = str(offer.status or "").strip().lower()
                if offer_status == "cerrado" and offer.vacancies_filled < offer.vacancies_total:
                    offer.status = JobOfferStatus.PUBLICADO
                    offer.is_active = 1
                    offer.filled_at = None

                offer.updated_at = datetime.now()
                session.add(offer)

        session.commit()
        session.refresh(application)
        return application

    # ----------------------------------------------------------------------
    # DELETE (hard delete como lo tenías)
    # ----------------------------------------------------------------------
    @staticmethod
    def delete_application(session: Session, application_id: int, user_id: int) -> bool:
        """Eliminar una postulación (solo el usuario que aplicó)"""
        application = session.get(JobApplication, application_id)
        if not application or application.user_id != user_id:
            return False

        session.delete(application)
        session.commit()
        return True

    # ----------------------------------------------------------------------
    # GET WITH USER INFO
    # ----------------------------------------------------------------------
    @staticmethod
    def get_application_with_user_info(
        session: Session,
        application_id: int
    ) -> Optional[dict]:
        """Obtener postulación con información del usuario"""
        query = select(
            JobApplication,
            AppUser.user,
            AppUser.email,
            AppUser.cv_summary
        ).join(
            AppUser, JobApplication.user_id == AppUser.id
        ).where(
            JobApplication.id == application_id
        )

        result = session.exec(query).first()
        if not result:
            return None

        application, user_name, user_email, cv_summary = result
        return {
            **application.model_dump(),
            "user_name": user_name,
            "user_email": user_email,
            "user_cv_summary": cv_summary
        }

    # ----------------------------------------------------------------------
    # GET WITH OFFER INFO
    # ----------------------------------------------------------------------
    @staticmethod
    def get_application_with_offer_info(
        session: Session,
        application_id: int
    ) -> Optional[dict]:
        """Obtener postulación con información de la oferta"""
        query = select(
            JobApplication,
            JobOffer.title,
            JobOffer.company,
            JobOffer.location
        ).join(
            JobOffer, JobApplication.job_offer_id == JobOffer.id
        ).where(
            JobApplication.id == application_id
        )

        result = session.exec(query).first()
        if not result:
            return None

        application, job_title, company, location = result
        return {
            **application.model_dump(),
            "job_title": job_title,
            "company": company,
            "location": location
        }

    # ----------------------------------------------------------------------
    # GET ALL BY USER + OFFER DATA  ✅ FIX PARA RESEÑAS BARISTA
    # ----------------------------------------------------------------------
    @staticmethod
    def get_applications_by_user_with_offer(
        session: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """Obtener todas las postulaciones de un usuario con información de las ofertas"""

        query = select(
            JobApplication,
            JobOffer.title,
            JobOffer.company,
            JobOffer.location,
            JobOffer.created_by   # ✅ NECESARIO PARA SABER employer_id
        ).join(
            JobOffer, JobApplication.job_offer_id == JobOffer.id
        ).where(
            JobApplication.user_id == user_id
        ).offset(skip).limit(limit).order_by(JobApplication.applied_at.desc())

        results = session.exec(query).all()

        applications = []
        for application, job_title, company, location, created_by in results:
            applications.append({
                **application.model_dump(),

                # datos de oferta (ya estaban)
                "job_title": job_title,
                "company": company,
                "location": location,

                # ✅ NUEVO: esto usa el front para toUserId cuando reseña el barista
                "employer_id": created_by,

                "rejection_reason": application.rejection_reason,
                "rejection_note": application.rejection_note,
                "rejected_at": application.rejected_at,
            })

        return applications

    # ----------------------------------------------------------------------
    # BULK UPDATE STATUS (IDS)
    # ----------------------------------------------------------------------
    @staticmethod
    def bulk_update_status(
        session: Session,
        application_ids: List[int],
        status: ApplicationStatus,
        recruiter_notes: Optional[str] = None
    ) -> List[int]:
        """Actualizar el estado de múltiples postulaciones a la vez"""

        query = select(JobApplication).where(JobApplication.id.in_(application_ids))
        applications = session.exec(query).all()

        updated_ids = []
        for app in applications:
            app.status = status
            if recruiter_notes is not None:
                app.recruiter_notes = recruiter_notes
            app.updated_at = datetime.now()
            session.add(app)
            updated_ids.append(app.id)

        session.commit()
        return updated_ids

    # ----------------------------------------------------------------------
    # BULK UPDATE BY JOB OFFER
    # ----------------------------------------------------------------------
    @staticmethod
    def bulk_update_by_job_offer(
        session: Session,
        job_offer_id: int,
        status: ApplicationStatus,
        exclude_ids: Optional[List[int]] = None,
        recruiter_notes: Optional[str] = None
    ) -> List[int]:
        """
        Actualizar el estado de todas las postulaciones de una oferta,
        excluyendo opcionalmente algunos IDs (por ejemplo, los seleccionados)
        """

        query = select(JobApplication).where(
            JobApplication.job_offer_id == job_offer_id
        )

        if exclude_ids:
            query = query.where(~JobApplication.id.in_(exclude_ids))

        applications = session.exec(query).all()

        updated_ids = []
        for app in applications:
            app.status = status
            if recruiter_notes is not None:
                app.recruiter_notes = recruiter_notes
            app.updated_at = datetime.now()
            session.add(app)
            updated_ids.append(app.id)

        session.commit()
        return updated_ids

    # ----------------------------------------------------------------------
    # COMPLETE APPLICATION (uno marca, otro confirma)
    # ----------------------------------------------------------------------
    @staticmethod
    def complete_application(
        session: Session,
        application_id: int,
        actor_user_id: int,
        actor_role: str  # "employer" | "worker"
    ) -> Optional[JobApplication]:

        application = session.get(JobApplication, application_id)
        if not application:
            return None

        actor_role = str(actor_role or "").strip().lower()
        if actor_role not in ("employer", "worker"):
            raise HTTPException(status_code=400, detail="actor_role inválido")

        current_status = str(
            application.status.value if hasattr(application.status, "value")
            else application.status or ""
        ).strip().lower()

        allowed_statuses = {
            ApplicationStatus.HIRED.value,
            ApplicationStatus.COMPLETED_BY_EMPLOYER.value,
            ApplicationStatus.COMPLETED_BY_WORKER.value,
            ApplicationStatus.COMPLETED_CONFIRMED.value
        }
        if current_status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="No se puede completar una postulación en este estado")

        # Validaciones por rol
        if actor_role == "worker":
            if application.user_id != actor_user_id:
                raise HTTPException(status_code=403, detail="Solo el postulante puede completar como worker")

        elif actor_role == "employer":
            offer = session.get(JobOffer, application.job_offer_id)
            if not offer:
                raise HTTPException(status_code=404, detail="Oferta no encontrada")

            # Soporta distintos nombres de campo en JobOffer
            owner_id = (
                getattr(offer, "owner_id", None)
                or getattr(offer, "user_id", None)
                or getattr(offer, "created_by", None)
            )
            if owner_id is not None and owner_id != actor_user_id:
                raise HTTPException(status_code=403, detail="Solo el ofertador puede completar como employer")

        # ---------------------------------------------
        # CAMBIOS DE ESTADO SEGÚN EL ROL
        # ---------------------------------------------
        if current_status == ApplicationStatus.HIRED.value:
            application.status = (
                ApplicationStatus.COMPLETED_BY_EMPLOYER
                if actor_role == "employer"
                else ApplicationStatus.COMPLETED_BY_WORKER
            )

        elif current_status == ApplicationStatus.COMPLETED_BY_EMPLOYER.value:
            if actor_role == "worker":
                application.status = ApplicationStatus.COMPLETED_CONFIRMED

        elif current_status == ApplicationStatus.COMPLETED_BY_WORKER.value:
            if actor_role == "employer":
                application.status = ApplicationStatus.COMPLETED_CONFIRMED

        # ---------------------------------------------
        # IMPORTANTE:
        # NO marcar worker_reviewed/employer_reviewed aquí.
        # Esos flags se setean SOLO cuando se crea la reseña
        # en ReviewService.create_review().
        # ---------------------------------------------

        application.updated_at = datetime.now()
        session.add(application)
        session.commit()
        session.refresh(application)
        return application
