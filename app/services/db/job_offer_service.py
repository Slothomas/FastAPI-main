from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional
from sqlmodel import Session, select, func

from app.models.job_offer import JobOffer, JobOfferStatus
from app.models.job_application import JobApplication, ApplicationStatus
from app.schemas.job_offer import JobOfferCreate, JobOfferUpdate


class JobOfferService:
    """Servicio para gestionar ofertas de trabajo (gig marketplace)"""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    @staticmethod
    def create_job_offer(
        session: Session,
        job_offer_data: JobOfferCreate,
        user_id: int
    ) -> JobOffer:
        job_offer = JobOffer(
            **job_offer_data.model_dump(),
            created_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(job_offer)
        session.commit()
        session.refresh(job_offer)
        return job_offer

    # ------------------------------------------------------------------
    # GET BY ID
    # ------------------------------------------------------------------
    @staticmethod
    def get_job_offer_by_id(session: Session, job_offer_id: int) -> Optional[JobOffer]:
        return session.get(JobOffer, job_offer_id)

    # ------------------------------------------------------------------
    # LIST + FILTERS (los que metiste en controller)
    # ------------------------------------------------------------------
    @staticmethod
    def get_all_job_offers(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[int] = None,

        status: Optional[str] = None,
        urgency: Optional[str] = None,

        region: Optional[str] = None,
        comuna: Optional[str] = None,
        skill: Optional[str] = None,
        job_type: Optional[str] = None,
        created_by: Optional[int] = None,

        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,

        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[JobOffer]:

        q = select(JobOffer)

        # ----- filtros base -----
        if is_active is not None:
            q = q.where(JobOffer.is_active == is_active)

        if status:
            q = q.where(JobOffer.status == status)

        if urgency:
            q = q.where(JobOffer.urgency == urgency)

        # ----- filtros avanzados -----
        if region:
            q = q.where(func.lower(JobOffer.region) == region.strip().lower())

        if comuna:
            q = q.where(func.lower(JobOffer.comuna) == comuna.strip().lower())

        if job_type:
            q = q.where(JobOffer.job_type == job_type)

        if created_by:
            q = q.where(JobOffer.created_by == created_by)

        if skill:
            like_skill = f"%{skill.strip().lower()}%"
            q = q.where(func.lower(JobOffer.required_skills).like(like_skill))

        # salary_range es string; filtramos solo cuando es numérico
        if min_salary is not None or max_salary is not None:
            cleaned = func.replace(func.replace(JobOffer.salary_range, ".", ""), ",", "")
            try_cast = func.try_cast(cleaned, float)
            if min_salary is not None:
                q = q.where(try_cast >= min_salary)
            if max_salary is not None:
                q = q.where(try_cast <= max_salary)

        if date_from:
            q = q.where(JobOffer.date_start >= date_from)

        if date_to:
            q = q.where(JobOffer.date_end <= date_to)

        q = q.offset(skip).limit(limit).order_by(JobOffer.created_at.desc())
        return list(session.exec(q).all())

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------
    @staticmethod
    def search_job_offers(
        session: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobOffer]:
        like = f"%{search_term.strip().lower()}%"
        query = select(JobOffer).where(
            (func.lower(JobOffer.title).like(like)) |
            (func.lower(JobOffer.company).like(like)) |
            (func.lower(JobOffer.location).like(like)) |
            (func.lower(JobOffer.description).like(like)) |
            (func.lower(JobOffer.required_skills).like(like))
        ).offset(skip).limit(limit).order_by(JobOffer.created_at.desc())
        return list(session.exec(query).all())

    # ------------------------------------------------------------------
    # BY DATE RANGE (CREATED_AT)
    # ------------------------------------------------------------------
    @staticmethod
    def get_job_offers_by_date_range(
        session: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobOffer]:
        query = select(JobOffer).where(JobOffer.is_active == 1)

        if start_date:
            query = query.where(func.cast(JobOffer.created_at, func.DATE) >= start_date)

        if end_date:
            query = query.where(func.cast(JobOffer.created_at, func.DATE) <= end_date)

        query = query.offset(skip).limit(limit).order_by(JobOffer.created_at.desc())
        return list(session.exec(query).all())

    # ------------------------------------------------------------------
    # BY USER
    # ------------------------------------------------------------------
    @staticmethod
    def get_job_offers_by_user(
        session: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobOffer]:
        query = select(JobOffer).where(
            JobOffer.created_by == user_id
        ).offset(skip).limit(limit).order_by(JobOffer.created_at.desc())
        return list(session.exec(query).all())

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    @staticmethod
    def update_job_offer(
        session: Session,
        job_offer_id: int,
        job_offer_data: JobOfferUpdate
    ) -> Optional[JobOffer]:
        job_offer = session.get(JobOffer, job_offer_id)
        if not job_offer:
            return None

        update_data = job_offer_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job_offer, key, value)

        job_offer.updated_at = datetime.now()
        session.add(job_offer)
        session.commit()
        session.refresh(job_offer)
        return job_offer

    # ------------------------------------------------------------------
    # DELETE (SOFT)
    # ------------------------------------------------------------------
    @staticmethod
    def delete_job_offer(session: Session, job_offer_id: int) -> bool:
        job_offer = session.get(JobOffer, job_offer_id)
        if not job_offer:
            return False

        job_offer.is_active = 0
        job_offer.status = JobOfferStatus.CERRADO
        job_offer.updated_at = datetime.now()
        session.add(job_offer)
        session.commit()
        return True

    # ------------------------------------------------------------------
    # COUNT APPLICATIONS
    # ------------------------------------------------------------------
    @staticmethod
    def get_applications_count(session: Session, job_offer_id: int) -> int:
        query = select(func.count(JobApplication.id)).where(
            JobApplication.job_offer_id == job_offer_id
        )
        return session.exec(query).one()

    # ==============================================================
    #                  PUNTO 7 — MULTI-VACANTE
    # ==============================================================

    @staticmethod
    def select_application_and_close_offer(
        session: Session,
        job_offer_id: int,
        application_id: int,
        recruiter_notes: Optional[str] = None
    ) -> Optional[JobOffer]:
        """
        Selecciona una postulación como HIRED.
        Si se completan todos los cupos:
          - cierra oferta
          - rechaza el resto
        """

        offer = session.get(JobOffer, job_offer_id)
        if not offer or offer.is_active == 0:
            return None

        # validación cupos
        if offer.vacancies_filled >= offer.vacancies_total:
            return None  # ya no hay cupos disponibles

        selected_app = session.get(JobApplication, application_id)
        if not selected_app or selected_app.job_offer_id != job_offer_id:
            return None

        # evitar doble contratación misma postulación
        if selected_app.status == ApplicationStatus.HIRED:
            return offer

        # 1) marcar HIRED
        selected_app.status = ApplicationStatus.HIRED
        if recruiter_notes is not None:
            selected_app.recruiter_notes = recruiter_notes
        selected_app.updated_at = datetime.now()
        session.add(selected_app)

        # 2) aumentar cupos llenos
        offer.vacancies_filled += 1
        offer.selected_application_id = offer.selected_application_id or application_id
        offer.updated_at = datetime.now()

        # 3) si se llenó, cerrar + rechazar resto
        if offer.vacancies_filled >= offer.vacancies_total:
            offer.status = JobOfferStatus.CERRADO
            offer.is_active = 0
            offer.filled_at = datetime.now()

            others_q = select(JobApplication).where(
                JobApplication.job_offer_id == job_offer_id,
                JobApplication.status != ApplicationStatus.HIRED
            )
            others = session.exec(others_q).all()
            for app in others:
                app.status = ApplicationStatus.REJECTED
                app.updated_at = datetime.now()
                session.add(app)

        session.add(offer)
        session.commit()
        session.refresh(offer)
        return offer

    @staticmethod
    def close_offer(session: Session, job_offer_id: int) -> Optional[JobOffer]:
        """
        Cierra oferta sin seleccionar a nadie.
        """
        offer = session.get(JobOffer, job_offer_id)
        if not offer:
            return None

        offer.status = JobOfferStatus.CERRADO
        offer.is_active = 0
        offer.updated_at = datetime.now()
        session.add(offer)
        session.commit()
        session.refresh(offer)
        return offer

    @staticmethod
    def get_selected_application(
        session: Session,
        job_offer_id: int
    ) -> Optional[JobApplication]:
        offer = session.get(JobOffer, job_offer_id)
        if not offer or not offer.selected_application_id:
            return None
        return session.get(JobApplication, offer.selected_application_id)
