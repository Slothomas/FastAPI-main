# app/services/db/job_application_service.py

from datetime import datetime
from typing import List, Optional
import json
from sqlmodel import Session, select
from fastapi import HTTPException

# schemas
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationUpdateStatus
)

# models
from app.models.job_application import (
    JobApplication,
    ApplicationStatus,
    RejectionReason
)
from app.models.job_offer import JobOffer, JobOfferStatus
from app.services.db.matching_service import MatchingService
from app.models.user import AppUser

# 🔔 servicio de notificaciones
from app.services.db.notification_service import NotificationService


class JobApplicationService:
    """Servicio para gestionar postulaciones a ofertas de trabajo"""

    # ----------------------------------------------------------------------
    # CREATE
    # ----------------------------------------------------------------------
    @staticmethod
    def create_application(session: Session, application_data: JobApplicationCreate, user_id: int) -> Optional[JobApplication]:
        """Crear una nueva postulación"""

        job_offer = session.get(JobOffer, application_data.job_offer_id)
        if not job_offer or job_offer.is_active == 0:
            return None

        # Verificar si ya aplicó
        existing = session.exec(
            select(JobApplication).where(
                JobApplication.job_offer_id == application_data.job_offer_id,
                JobApplication.user_id == user_id
            )
        ).first()

        if existing:
            return None

        # Matching persistido
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
    # REFRESH MATCHING SCORE
    # ----------------------------------------------------------------------
    @staticmethod
    def refresh_matching_score(session: Session, application_id: int) -> Optional[JobApplication]:
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
        return session.get(JobApplication, application_id)

    # ----------------------------------------------------------------------
    # GET BY USER
    # ----------------------------------------------------------------------
    @staticmethod
    def get_applications_by_user(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[JobApplication]:
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
    def get_applications_by_job_offer(session: Session, job_offer_id: int, skip: int = 0, limit: int = 100) -> List[JobApplication]:
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
    def update_application_status(session: Session, application_id: int, status_data: JobApplicationUpdateStatus) -> Optional[JobApplication]:
        application = session.get(JobApplication, application_id)
        if not application:
            return None

        old_status = str(application.status.value if hasattr(application.status, "value") else application.status or "").strip().lower()
        new_status = str(status_data.status or "").strip().lower()

        # Validar enum
        valid_statuses = {s.value for s in ApplicationStatus}
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail="status inválido")

        application.status = ApplicationStatus(new_status)

        if status_data.recruiter_notes is not None:
            application.recruiter_notes = status_data.recruiter_notes

        # ----- rechazo -----
        if new_status == "rejected":
            if not status_data.rejection_reason:
                raise HTTPException(status_code=400, detail="rejection_reason es obligatorio")

            valid_reasons = {r.value for r in RejectionReason}
            if status_data.rejection_reason not in valid_reasons:
                raise HTTPException(status_code=400, detail="rejection_reason inválido")

            application.rejection_reason = status_data.rejection_reason
            application.rejection_note = status_data.rejection_note
            application.rejected_at = datetime.now()

        else:
            application.rejection_reason = None
            application.rejection_note = None
            application.rejected_at = None

        application.updated_at = datetime.now()
        session.add(application)

        # ------- vacantes -------
        offer = session.get(JobOffer, application.job_offer_id)
        if offer:
            offer.vacancies_filled = offer.vacancies_filled or 0
            offer.vacancies_total = offer.vacancies_total or 1

            # hired → rejected: liberar vacante
            if old_status == "hired" and new_status == "rejected":
                offer.vacancies_filled = max(0, offer.vacancies_filled - 1)

                if str(offer.status).lower() == "cerrado" and offer.vacancies_filled < offer.vacancies_total:
                    offer.status = JobOfferStatus.PUBLICADO
                    offer.is_active = 1
                    offer.filled_at = None

                offer.updated_at = datetime.now()
                session.add(offer)

        session.commit()
        session.refresh(application)

        # ----------------------------------------------------------------------
        # 🔔 NOTIFICACIONES POR CAMBIO DE ESTADO
        # ----------------------------------------------------------------------

        offer = session.get(JobOffer, application.job_offer_id)

        # ACEPTADO
        if new_status == ApplicationStatus.HIRED.value:
            NotificationService.create_notification(
                session=session,
                user_id=application.user_id,
                type="application_status",
                title="¡Fuiste aceptado! 🎉",
                message=f"Has sido aceptado en la oferta '{offer.title}' de {offer.company}.",
                payload={"application_id": application.id, "job_offer_id": offer.id, "status": "hired"}
            )

        # RECHAZADO
        elif new_status == ApplicationStatus.REJECTED.value:
            NotificationService.create_notification(
                session=session,
                user_id=application.user_id,
                type="application_status",
                title="Tu postulación fue rechazada",
                message=f"No fuiste seleccionado para la oferta '{offer.title}'.",
                payload={"application_id": application.id, "job_offer_id": offer.id, "status": "rejected"}
            )

        return application

    # ----------------------------------------------------------------------
    # DELETE
    # ----------------------------------------------------------------------
    @staticmethod
    def delete_application(session: Session, application_id: int, user_id: int) -> bool:
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
    def get_application_with_user_info(session: Session, application_id: int) -> Optional[dict]:
        query = select(
            JobApplication,
            AppUser.user,
            AppUser.email,
            AppUser.cv_summary
        ).join(
            AppUser, JobApplication.user_id == AppUser.id
        ).where(JobApplication.id == application_id)

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
    def get_application_with_offer_info(session: Session, application_id: int) -> Optional[dict]:
        query = select(
            JobApplication,
            JobOffer.title,
            JobOffer.company,
            JobOffer.location
        ).join(
            JobOffer, JobApplication.job_offer_id == JobOffer.id
        ).where(JobApplication.id == application_id)

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
    # GET ALL BY USER + OFFER DATA
    # ----------------------------------------------------------------------
    @staticmethod
    def get_applications_by_user_with_offer(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:

        query = select(
            JobApplication,
            JobOffer.title,
            JobOffer.company,
            JobOffer.location,
            JobOffer.created_by,
            JobOffer.salary_range
        ).join(
            JobOffer, JobApplication.job_offer_id == JobOffer.id
        ).where(JobApplication.user_id == user_id)\
         .offset(skip).limit(limit)\
         .order_by(JobApplication.applied_at.desc())

        rows = session.exec(query).all()

        apps = []
        for app, title, company, location, created_by, salary_range in rows:
            apps.append({
                **app.model_dump(),
                "job_title": title,
                "company": company,
                "location": location,
                "employer_id": created_by,
                "job_offer_salary_range": salary_range
            })
        return apps

    # ----------------------------------------------------------------------
    # BULK UPDATE STATUS
    # ----------------------------------------------------------------------
    @staticmethod
    def bulk_update_status(session: Session, application_ids: List[int], status: ApplicationStatus, recruiter_notes: Optional[str] = None) -> List[int]:

        query = select(JobApplication).where(JobApplication.id.in_(application_ids))
        apps = session.exec(query).all()

        updated_ids = []
        for app in apps:
            app.status = status
            if recruiter_notes is not None:
                app.recruiter_notes = recruiter_notes
            app.updated_at = datetime.now()
            session.add(app)
            updated_ids.append(app.id)

        session.commit()
        return updated_ids

    # ----------------------------------------------------------------------
    # BULK UPDATE BY OFFER
    # ----------------------------------------------------------------------
    @staticmethod
    def bulk_update_by_job_offer(session: Session, job_offer_id: int, status: ApplicationStatus, exclude_ids: Optional[List[int]] = None, recruiter_notes: Optional[str] = None) -> List[int]:

        query = select(JobApplication).where(JobApplication.job_offer_id == job_offer_id)

        if exclude_ids:
            query = query.where(~JobApplication.id.in_(exclude_ids))

        apps = session.exec(query).all()

        updated_ids = []
        for app in apps:
            app.status = status
            if recruiter_notes is not None:
                app.recruiter_notes = recruiter_notes
            app.updated_at = datetime.now()
            session.add(app)
            updated_ids.append(app.id)

        session.commit()
        return updated_ids

    # ----------------------------------------------------------------------
    # COMPLETE APPLICATION (worker/employer)
    # ----------------------------------------------------------------------
    @staticmethod
    def complete_application(session: Session, application_id: int, actor_user_id: int, actor_role: str) -> Optional[JobApplication]:

        application = session.get(JobApplication, application_id)
        if not application:
            return None

        actor_role = actor_role.strip().lower()
        if actor_role not in ("employer", "worker"):
            raise HTTPException(status_code=400, detail="actor_role inválido")

        current_status = str(application.status.value if hasattr(application.status, "value") else application.status).lower()

        allowed = {
            ApplicationStatus.HIRED.value,
            ApplicationStatus.COMPLETED_BY_EMPLOYER.value,
            ApplicationStatus.COMPLETED_BY_WORKER.value,
            ApplicationStatus.COMPLETED_CONFIRMED.value
        }
        if current_status not in allowed:
            raise HTTPException(status_code=400, detail="No se puede completar en este estado")

        # Validaciones por rol
        if actor_role == "worker" and application.user_id != actor_user_id:
            raise HTTPException(status_code=403, detail="Solo el postulante puede completar")

        if actor_role == "employer":
            offer = session.get(JobOffer, application.job_offer_id)
            if not offer:
                raise HTTPException(status_code=404, detail="Oferta no encontrada")

            owner_id = getattr(offer, "created_by", None) or getattr(offer, "user_id", None)
            if owner_id != actor_user_id:
                raise HTTPException(status_code=403, detail="Solo el ofertante puede confirmar")

        # Cambio de estado
        if current_status == ApplicationStatus.HIRED.value:
            application.status = (
                ApplicationStatus.COMPLETED_BY_EMPLOYER
                if actor_role == "employer"
                else ApplicationStatus.COMPLETED_BY_WORKER
            )

        elif current_status == ApplicationStatus.COMPLETED_BY_EMPLOYER.value and actor_role == "worker":
            application.status = ApplicationStatus.COMPLETED_CONFIRMED

        elif current_status == ApplicationStatus.COMPLETED_BY_WORKER.value and actor_role == "employer":
            application.status = ApplicationStatus.COMPLETED_CONFIRMED

        application.updated_at = datetime.now()
        session.add(application)
        session.commit()
        session.refresh(application)

        # ------------------------------------------------------------------
        # 🔔 NOTIFICACIONES DEL FLUJO DE COMPLETADO
        # ------------------------------------------------------------------
        offer = session.get(JobOffer, application.job_offer_id)
        owner_id = getattr(offer, "created_by", None) or getattr(offer, "user_id", None)

        # 1) Worker completó → avisar employer
        if application.status == ApplicationStatus.COMPLETED_BY_WORKER:
            NotificationService.create_notification(
                session=session,
                user_id=owner_id,
                type="job_completed",
                title="El barista marcó el trabajo como completado",
                message=f"El barista completó el trabajo '{offer.title}'. Falta tu confirmación.",
                payload={"application_id": application.id, "job_offer_id": offer.id}
            )

        # 2) Employer completó → avisar worker
        elif application.status == ApplicationStatus.COMPLETED_BY_EMPLOYER:
            NotificationService.create_notification(
                session=session,
                user_id=application.user_id,
                type="job_completed",
                title="El empleador marcó el trabajo como completado",
                message=f"El empleador marcó '{offer.title}' como completado. Falta tu confirmación.",
                payload={"application_id": application.id, "job_offer_id": offer.id}
            )

        # 3) Confirmado por ambos
        elif application.status == ApplicationStatus.COMPLETED_CONFIRMED:

            # Avisar a worker
            NotificationService.create_notification(
                session=session,
                user_id=application.user_id,
                type="job_completed_final",
                title="Trabajo completado ✔️",
                message=f"El trabajo '{offer.title}' fue confirmado por ambas partes.",
                payload={"application_id": application.id, "job_offer_id": offer.id}
            )

            # Avisar a employer
            NotificationService.create_notification(
                session=session,
                user_id=owner_id,
                type="job_completed_final",
                title="Trabajo completado ✔️",
                message=f"Se confirmó el trabajo '{offer.title}'.",
                payload={"application_id": application.id, "job_offer_id": offer.id}
            )

        return application
