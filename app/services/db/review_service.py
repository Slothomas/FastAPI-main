from datetime import datetime
from typing import List, Tuple
from sqlmodel import Session, select, func
from fastapi import HTTPException

from app.models.review import Review
from app.models.user_profile import UserProfile
from app.schemas.review import ReviewCreate
from app.models.job_application import JobApplication, ApplicationStatus
from app.models.job_offer import JobOffer


class ReviewService:
    @staticmethod
    def create_review(session: Session, reviewer_id: int, payload: ReviewCreate):
        # 1) Traer postulación
        app = session.get(JobApplication, payload.application_id)
        if not app:
            raise HTTPException(404, "Postulación no encontrada")

        # 2) Validar estado completado (blindado)
        status_norm = str(
            app.status.value if hasattr(app.status, "value") else app.status
        ).strip().lower()

        if status_norm != ApplicationStatus.COMPLETED_CONFIRMED.value:
            raise HTTPException(400, "Solo puedes reseñar trabajos completados")

        # 3) Traer oferta
        offer = session.get(JobOffer, app.job_offer_id)
        if not offer:
            raise HTTPException(404, "Oferta no encontrada")

        # 4) Identificar roles reales
        employer_id = getattr(offer, "created_by", None)  # campo real
        worker_id = app.user_id

        if employer_id is None:
            raise HTTPException(500, "Oferta sin dueño (created_by missing)")

        is_employer = reviewer_id == employer_id
        is_worker = reviewer_id == worker_id

        if not (is_employer or is_worker):
            raise HTTPException(403, "No puedes reseñar esta postulación")

        # 5) Evitar doble reseña por rol
        if is_worker and app.worker_reviewed:
            raise HTTPException(400, "El barista ya dejó reseña")
        if is_employer and app.employer_reviewed:
            raise HTTPException(400, "El empleador ya dejó reseña")

        # 6) Definir reviewee (a quién reseñan)
        reviewee_id = employer_id if is_worker else worker_id

        # 7) Crear reseña
        review = Review(
            application_id=app.id,
            job_offer_id=offer.id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            rating=float(payload.rating),  # asegurar float
            topic=payload.topic,
            comment=payload.comment,
            is_active=True,
        )
        session.add(review)

        # 8) Marcar flag en job_application
        if is_worker:
            app.worker_reviewed = True
        else:
            app.employer_reviewed = True

        app.updated_at = datetime.utcnow()
        session.add(app)

        session.commit()
        session.refresh(review)

        # 9) Recalcular reputación del evaluado
        ReviewService.recalculate_user_rating(session, reviewee_id)

        return review

    # ------------------------------------------------------------------
    @staticmethod
    def get_reviews_for_user(session: Session, user_id: int) -> List[Review]:
        q = select(Review).where(
            Review.reviewee_id == user_id,
            Review.is_active == True
        ).order_by(Review.created_at.desc())
        return list(session.exec(q).all())

    @staticmethod
    def get_reviews_summary_for_user(session: Session, user_id: int) -> Tuple[float, int]:
        avg_rating, cnt = session.exec(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.reviewee_id == user_id, Review.is_active == True
            )
        ).one()
        cnt = int(cnt or 0)
        avg_rating = round(float(avg_rating), 2) if avg_rating is not None else 0.0
        return avg_rating, cnt

    @staticmethod
    def recalculate_user_rating(session: Session, user_id: int) -> None:
        avg_rating, cnt = ReviewService.get_reviews_summary_for_user(session, user_id)
        profile = session.exec(
            select(UserProfile).where(UserProfile.user_id == user_id)
        ).first()

        if profile:
            profile.rating_avg = avg_rating if cnt > 0 else None
            profile.reviews_count = cnt
            profile.updated_at = datetime.utcnow()
            session.add(profile)
            session.commit()

    @staticmethod
    def delete_review(session: Session, review_id: int, requester_id: int) -> bool:
        review = session.get(Review, review_id)
        if not review or review.is_active is False:
            return False

        if review.reviewer_id != requester_id:
            return False

        review.is_active = False
        session.add(review)
        session.commit()

        ReviewService.recalculate_user_rating(session, review.reviewee_id)
        return True
