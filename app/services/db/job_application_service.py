from datetime import datetime
from typing import List, Optional
import json

from sqlmodel import Session, select

from app.models.job_application import JobApplication, ApplicationStatus
from app.models.job_offer import JobOffer
from app.models.user import AppUser
from app.schemas.job_application import JobApplicationCreate, JobApplicationUpdateStatus
from app.services.db.matching_service import MatchingService


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
        """Actualizar el estado de una postulación (solo reclutador)"""

        application = session.get(JobApplication, application_id)
        if not application:
            return None

        application.status = status_data.status

        if status_data.recruiter_notes is not None:
            application.recruiter_notes = status_data.recruiter_notes

        application.updated_at = datetime.now()

        session.add(application)
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
    # GET ALL BY USER + OFFER DATA
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
            JobOffer.location
        ).join(
            JobOffer, JobApplication.job_offer_id == JobOffer.id
        ).where(
            JobApplication.user_id == user_id
        ).offset(skip).limit(limit).order_by(JobApplication.applied_at.desc())

        results = session.exec(query).all()

        applications = []
        for application, job_title, company, location in results:
            applications.append({
                **application.model_dump(),
                "job_title": job_title,
                "company": company,
                "location": location
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
