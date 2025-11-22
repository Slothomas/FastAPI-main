# app/services/db/review_service.py
from datetime import datetime
from typing import List, Optional, Tuple
from sqlmodel import Session, select, func

from app.models.review import Review
from app.models.user_profile import UserProfile
from app.schemas.review import ReviewCreate


class ReviewService:

    @staticmethod
    def create_review(
        session: Session,
        reviewer_id: int,
        data: ReviewCreate
    ) -> Optional[Review]:
        """
        Crea una review evitando duplicados.
        Luego recalcula rating_avg y reviews_count del worker.
        """

        # Evitar doble review por misma oferta y reviewer
        existing = session.exec(
            select(Review).where(
                Review.job_offer_id == data.job_offer_id,
                Review.reviewer_id == reviewer_id,
                Review.reviewee_id == data.reviewee_id,
                Review.is_active == True
            )
        ).first()

        if existing:
            return None

        review = Review(
            job_offer_id=data.job_offer_id,
            reviewer_id=reviewer_id,
            reviewee_id=data.reviewee_id,
            rating=float(data.rating),
            comment=data.comment,
            created_at=datetime.utcnow(),
            is_active=True
        )

        session.add(review)
        session.commit()
        session.refresh(review)

        # Recalcular reputación del evaluado
        ReviewService.recalculate_user_rating(session, data.reviewee_id)

        return review

    @staticmethod
    def get_reviews_for_user(session: Session, user_id: int) -> List[Review]:
        """
        Lista reviews activas para un worker.
        """
        q = select(Review).where(
            Review.reviewee_id == user_id,
            Review.is_active == True
        ).order_by(Review.created_at.desc())

        return list(session.exec(q).all())

    @staticmethod
    def get_reviews_summary_for_user(session: Session, user_id: int) -> Tuple[float, int]:
        """
        Devuelve (avg, count) de reviews activas para worker.
        """
        avg_rating, cnt = session.exec(
            select(
                func.avg(Review.rating),
                func.count(Review.id)
            ).where(
                Review.reviewee_id == user_id,
                Review.is_active == True
            )
        ).one()

        cnt = int(cnt or 0)
        avg_rating = round(float(avg_rating), 2) if avg_rating is not None else 0.0

        return avg_rating, cnt

    @staticmethod
    def recalculate_user_rating(session: Session, user_id: int) -> None:
        """
        Recalcula rating_avg y reviews_count en app_user_profile.
        """
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
        """
        Soft delete: solo puede eliminar quien creó la review.
        """
        review = session.get(Review, review_id)
        if not review or review.is_active == False:
            return False

        if review.reviewer_id != requester_id:
            return False

        review.is_active = False
        session.add(review)
        session.commit()

        ReviewService.recalculate_user_rating(session, review.reviewee_id)

        return True
