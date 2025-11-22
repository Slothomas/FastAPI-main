from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select

from app.models.user_favorite_offer import UserFavoriteOffer
from app.models.user_favorite_worker import UserFavoriteWorker
from app.models.job_offer import JobOffer
from app.models.user_profile import UserProfile
from app.models.user import AppUser


class FavoritesService:

    # ==========================================================
    # FAVORITE OFFERS (worker -> offers)
    # ==========================================================

    @staticmethod
    def add_favorite_offer(session: Session, user_id: int, job_offer_id: int) -> Optional[UserFavoriteOffer]:
        # evita duplicados activos
        existing = session.exec(
            select(UserFavoriteOffer).where(
                UserFavoriteOffer.user_id == user_id,
                UserFavoriteOffer.job_offer_id == job_offer_id
            )
        ).first()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.created_at = datetime.now()
                session.add(existing)
                session.commit()
                session.refresh(existing)
            return existing

        fav = UserFavoriteOffer(
            user_id=user_id,
            job_offer_id=job_offer_id,
            is_active=True,
            created_at=datetime.now()
        )
        session.add(fav)
        session.commit()
        session.refresh(fav)
        return fav

    @staticmethod
    def remove_favorite_offer(session: Session, user_id: int, job_offer_id: int) -> bool:
        fav = session.exec(
            select(UserFavoriteOffer).where(
                UserFavoriteOffer.user_id == user_id,
                UserFavoriteOffer.job_offer_id == job_offer_id,
                UserFavoriteOffer.is_active == True
            )
        ).first()

        if not fav:
            return False

        fav.is_active = False
        session.add(fav)
        session.commit()
        return True

    @staticmethod
    def list_favorite_offers(session: Session, user_id: int) -> List[dict]:
        q = (
            select(UserFavoriteOffer, JobOffer)
            .join(JobOffer, UserFavoriteOffer.job_offer_id == JobOffer.id)
            .where(
                UserFavoriteOffer.user_id == user_id,
                UserFavoriteOffer.is_active == True
            )
            .order_by(UserFavoriteOffer.created_at.desc())
        )

        rows = session.exec(q).all()
        result = []
        for fav, offer in rows:
            result.append({
                "favorite_id": fav.id,
                "job_offer_id": offer.id,
                "title": offer.title,
                "company": offer.company,
                "location": getattr(offer, "location", None),
                "salary_range": getattr(offer, "salary_range", None),
                "date_start": getattr(offer, "date_start", None),
                "date_end": getattr(offer, "date_end", None),
                "created_at": fav.created_at,
            })
        return result

    # ==========================================================
    # FAVORITE WORKERS (client -> workers)
    # ==========================================================

    @staticmethod
    def add_favorite_worker(session: Session, client_user_id: int, worker_user_id: int) -> Optional[UserFavoriteWorker]:
        existing = session.exec(
            select(UserFavoriteWorker).where(
                UserFavoriteWorker.client_user_id == client_user_id,
                UserFavoriteWorker.worker_user_id == worker_user_id
            )
        ).first()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.created_at = datetime.now()
                session.add(existing)
                session.commit()
                session.refresh(existing)
            return existing

        fav = UserFavoriteWorker(
            client_user_id=client_user_id,
            worker_user_id=worker_user_id,
            is_active=True,
            created_at=datetime.now()
        )
        session.add(fav)
        session.commit()
        session.refresh(fav)
        return fav

    @staticmethod
    def remove_favorite_worker(session: Session, client_user_id: int, worker_user_id: int) -> bool:
        fav = session.exec(
            select(UserFavoriteWorker).where(
                UserFavoriteWorker.client_user_id == client_user_id,
                UserFavoriteWorker.worker_user_id == worker_user_id,
                UserFavoriteWorker.is_active == True
            )
        ).first()

        if not fav:
            return False

        fav.is_active = False
        session.add(fav)
        session.commit()
        return True

    @staticmethod
    def list_favorite_workers(session: Session, client_user_id: int) -> List[dict]:
        q = (
            select(UserFavoriteWorker, UserProfile, AppUser)
            .join(UserProfile, UserFavoriteWorker.worker_user_id == UserProfile.user_id)
            .join(AppUser, UserFavoriteWorker.worker_user_id == AppUser.id)
            .where(
                UserFavoriteWorker.client_user_id == client_user_id,
                UserFavoriteWorker.is_active == True
            )
            .order_by(UserFavoriteWorker.created_at.desc())
        )

        rows = session.exec(q).all()
        result = []
        for fav, prof, user in rows:
            result.append({
                "favorite_id": fav.id,
                "worker_user_id": prof.user_id,
                "full_name": getattr(prof, "full_name", None) or getattr(user, "user", None),
                "bio": getattr(prof, "bio", None),
                "skills": getattr(prof, "skills", None),
                "avatar_url": getattr(prof, "avatar_url", None),
                "rating_avg": getattr(prof, "rating_avg", None),
                "reviews_count": getattr(prof, "reviews_count", 0),
                "created_at": fav.created_at,
            })
        return result
