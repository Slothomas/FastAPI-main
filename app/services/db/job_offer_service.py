from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional
from sqlmodel import Session, select, func, or_

# Importamos todos los Enums para hacer comparaciones seguras
from app.models.job_offer import JobOffer, JobOfferStatus, JobType, UrgencyType
from app.models.job_application import JobApplication, ApplicationStatus
from app.schemas.job_offer import JobOfferCreate, JobOfferUpdate

# ✅ NUEVO: modelos multi-local
from app.models.business import Business
from app.models.business_location import BusinessLocation


class JobOfferService:
    """Servicio para gestionar ofertas de trabajo (gig marketplace)"""

    # ------------------------------------------------------------------
    # CREATE  (multi-local ready sin romper legacy)
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # CREATE  (multi-local ready sin romper legacy)
    # ------------------------------------------------------------------
    @staticmethod
    def create_job_offer(
        session: Session,
        job_offer_data: JobOfferCreate,
        user_id: int
    ) -> JobOffer:
        data = job_offer_data.model_dump()

        # ==========================================================
        # ✅ SOPORTE MULTI-LOCAL (nuevo modelo)
        # - Si viene location_id, autopoblamos campos legacy
        # - Validamos ownership del negocio
        # - Validamos coherencia negocio <-> sede
        # ==========================================================
        business_id = data.get("business_id")
        location_id = data.get("location_id")

        # Si viene location_id, cargamos sede y negocio
        if location_id:
            loc = session.get(BusinessLocation, location_id)
            if not loc:
                raise ValueError("BusinessLocation no existe")

            biz = session.get(Business, loc.business_id)
            if not biz:
                raise ValueError("Business asociado no existe")

            # validar dueño (nuevo nombre: owner_id)
            if biz.owner_id != user_id:
                raise ValueError("No puedes publicar ofertas para un negocio que no es tuyo")

            # si además venía business_id, validar consistencia
            if business_id and business_id != biz.id:
                raise ValueError("La sede no pertenece al negocio indicado")

            # autopoblar campos legacy desde negocio/local
            data["business_id"] = biz.id
            data["company"] = biz.name
            data["location"] = loc.name  # o loc.address si prefieres dirección
            data["region"] = loc.region or data.get("region")
            data["comuna"] = loc.comuna or data.get("comuna")

        # Si viene business_id pero NO location_id, validar dueño igual
        elif business_id:
            biz = session.get(Business, business_id)
            if not biz:
                raise ValueError("Business no existe")

            if biz.owner_id != user_id:
                raise ValueError("No puedes publicar ofertas para un negocio que no es tuyo")

            data["business_id"] = biz.id
            # company lo puedes dejar como venía o autopoblarla
            data["company"] = data.get("company") or biz.name

        # Defaults defensivos
        if data.get("vacancies_total") is None:
            data["vacancies_total"] = 1
        if data.get("vacancies_filled") is None:
            data["vacancies_filled"] = 0
        if data.get("is_active") is None:
            data["is_active"] = 1

        # Enums defensivos (por si viene string)
        if isinstance(data.get("status"), str):
            data["status"] = data["status"].upper()
        if isinstance(data.get("urgency"), str):
            data["urgency"] = data["urgency"].upper()
        if isinstance(data.get("job_type"), str):
            data["job_type"] = data["job_type"].upper()

        job_offer = JobOffer(
            **data,
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
    # LIST + FILTERS
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
            q = q.where(JobOffer.status == status.upper())

        if urgency:
            q = q.where(JobOffer.urgency == urgency.upper())

        # ----- filtros avanzados -----
        if region:
            q = q.where(func.lower(JobOffer.region) == region.strip().lower())

        if comuna:
            q = q.where(func.lower(JobOffer.comuna) == comuna.strip().lower())

        if job_type:
            q = q.where(JobOffer.job_type == job_type.upper())

        if created_by:
            q = q.where(JobOffer.created_by == created_by)

        if skill:
            like_skill = f"%{skill.strip().lower()}%"
            q = q.where(func.lower(func.coalesce(JobOffer.required_skills, '')).like(like_skill))

        # Filtro de Salario (SQL Server Safe)
        if min_salary is not None:
            q = q.where(JobOffer.salary_range >= min_salary)

        if max_salary is not None:
            q = q.where(JobOffer.salary_range <= max_salary)

        if date_from:
            q = q.where(JobOffer.date_start >= date_from)

        if date_to:
            q = q.where(JobOffer.date_end <= date_to)

        q = q.offset(skip).limit(limit).order_by(JobOffer.created_at.desc())
        return session.exec(q).all()

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
            or_(
                func.lower(JobOffer.title).like(like),
                func.lower(JobOffer.company).like(like),
                func.lower(func.coalesce(JobOffer.location, '')).like(like),
                func.lower(func.coalesce(JobOffer.description, '')).like(like),
                func.lower(func.coalesce(JobOffer.required_skills, '')).like(like)
            )
        ).offset(skip).limit(limit).order_by(JobOffer.created_at.desc())

        return session.exec(query).all()

    # ------------------------------------------------------------------
    # BY DATE RANGE
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
            query = query.where(func.cast(JobOffer.created_at, date) >= start_date)

        if end_date:
            query = query.where(func.cast(JobOffer.created_at, date) <= end_date)

        query = query.offset(skip).limit(limit).order_by(JobOffer.created_at.desc())
        return session.exec(query).all()

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

        return session.exec(query).all()

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
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

        # ==========================================================
        # ✅ Si cambian business_id / location_id => validar coherencia
        # ==========================================================
        new_business_id = update_data.get("business_id")
        new_location_id = update_data.get("location_id")

        if new_location_id:
            loc = session.get(BusinessLocation, new_location_id)
            if not loc:
                raise ValueError("BusinessLocation no existe")

            biz = session.get(Business, loc.business_id)
            if not biz:
                raise ValueError("Business asociado no existe")

            # si además venía business_id, validar consistencia
            if new_business_id and new_business_id != biz.id:
                raise ValueError("La sede no pertenece al negocio indicado")

            # autopoblar campos legacy
            update_data["business_id"] = biz.id
            update_data["company"] = biz.name
            update_data["location"] = loc.name  # o loc.address
            update_data["region"] = loc.region or update_data.get("region")
            update_data["comuna"] = loc.comuna or update_data.get("comuna")

        elif new_business_id:
            biz = session.get(Business, new_business_id)
            if not biz:
                raise ValueError("Business no existe")

            update_data["business_id"] = biz.id
            update_data["company"] = update_data.get("company") or biz.name

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
    #                   MULTI-VACANTE
    # ==============================================================
    @staticmethod
    def select_application_and_close_offer(
        session: Session,
        job_offer_id: int,
        application_id: int,
        recruiter_notes: Optional[str] = None
    ) -> Optional[JobOffer]:

        offer = session.get(JobOffer, job_offer_id)
        if not offer:
            return None

        offer.vacancies_filled = offer.vacancies_filled or 0
        offer.is_active = offer.is_active if offer.is_active is not None else 1

        selected_app = session.get(JobApplication, application_id)
        if not selected_app or selected_app.job_offer_id != job_offer_id:
            return None

        if selected_app.status == ApplicationStatus.HIRED:
            return offer

        vacancies_total = offer.vacancies_total or 1

        if offer.vacancies_filled >= vacancies_total:
            return None

        selected_app.status = ApplicationStatus.HIRED
        if recruiter_notes:
            selected_app.recruiter_notes = recruiter_notes
        selected_app.updated_at = datetime.now()
        session.add(selected_app)

        offer.vacancies_filled += 1
        offer.updated_at = datetime.now()

        if not offer.selected_application_id:
            offer.selected_application_id = application_id

        if offer.vacancies_filled >= vacancies_total:
            offer.status = JobOfferStatus.CERRADO
            offer.is_active = 0
            offer.filled_at = datetime.now()

            others = session.exec(
                select(JobApplication).where(
                    JobApplication.job_offer_id == job_offer_id,
                    JobApplication.status != ApplicationStatus.HIRED
                )
            ).all()

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

    # ==============================================================
    # SELECT APPLICATION (solo seleccionar, NO cerrar aquí)
    # ==============================================================
    @staticmethod
    def select_application(
        session: Session,
        job_offer_id: int,
        application_id: int,
        recruiter_notes: Optional[str] = None
    ) -> Optional[JobOffer]:
        offer = session.get(JobOffer, job_offer_id)
        if not offer:
            return None

        if offer.vacancies_filled is None:
            offer.vacancies_filled = 0
        if offer.is_active is None:
            offer.is_active = 1
        if offer.status is None:
            offer.status = JobOfferStatus.PUBLICADO
        if offer.urgency is None:
            offer.urgency = UrgencyType.NORMAL

        selected_app = session.get(JobApplication, application_id)
        if not selected_app or selected_app.job_offer_id != job_offer_id:
            return None

        if selected_app.status == ApplicationStatus.HIRED:
            return offer

        vacancies_total = getattr(offer, "vacancies_total", 1)
        if offer.vacancies_filled >= vacancies_total:
            return None

        selected_app.status = ApplicationStatus.HIRED
        if recruiter_notes is not None:
            selected_app.recruiter_notes = recruiter_notes
        selected_app.updated_at = datetime.now()
        session.add(selected_app)

        offer.vacancies_filled += 1
        offer.selected_application_id = offer.selected_application_id or application_id
        offer.updated_at = datetime.now()

        session.add(offer)
        session.commit()
        session.refresh(offer)
        return offer
