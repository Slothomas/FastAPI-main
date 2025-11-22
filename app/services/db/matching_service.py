# app/services/db/matching_service.py
from __future__ import annotations

from typing import List, Optional, Tuple, Dict
from sqlmodel import Session, select, func

from app.models.job_offer import JobOffer
from app.models.user_profile import UserProfile
from app.models.user_certificate import UserCertificate
from app.models.user import AppUser
from app.schemas.matching import MatchingWorkerResult


class MatchingService:
    """
    Servicio de matching workers ↔ job_offer.

    Estrategia:
      - Skills match (peso alto)
      - Ubicación (region/comuna)
      - Disponibilidad
      - Tarifa vs salario ofertado
      - Reputación (rating_avg + reviews_count)
      - Certificados activos
    """

    # pesos (suman 100)
    W_SKILLS = 45
    W_LOCATION = 20
    W_AVAILABILITY = 10
    W_RATE = 10
    W_RATING = 10
    W_CERTS = 5

    # ===========================================================
    # HELPERS
    # ===========================================================

    @staticmethod
    def _parse_csv(s: Optional[str]) -> List[str]:
        if not s:
            return []
        return [x.strip().lower() for x in s.split(",") if x.strip()]

    @staticmethod
    def _simple_location_norm(s: Optional[str]) -> Optional[str]:
        return s.strip().lower() if s else None

    @staticmethod
    def _parse_salary(salary_range: Optional[str]) -> Optional[float]:
        """
        Intenta convertir salary_range en un número.
        Acepta:
            - "500000"
            - "500.000"
            - "500k"
            - "500000-700000" → toma el inferior
        """
        if not salary_range:
            return None

        raw = str(salary_range).lower().replace(".", "").replace(",", "").strip()

        if "-" in raw:
            raw = raw.split("-")[0]

        if "k" in raw:
            try:
                return float(raw.replace("k", "")) * 1000
            except:
                return None

        try:
            return float(raw)
        except:
            return None

    # ===========================================================
    # ► NUEVO PARA PUNTO 6 — matching de UN usuario específico
    # ===========================================================

    @classmethod
    def compute_match_for_user(
        cls,
        session: Session,
        job_offer_id: int,
        user_id: int
    ) -> Dict:
        """
        Calcula el matching para un usuario puntual.
        Retorna dict {"score": float, "breakdown": {...}}
        """

        # traemos el resultado global (es más barato que duplicar toda la lógica)
        results = cls.get_matching_workers_for_offer(
            session=session,
            job_offer_id=job_offer_id,
            limit=500
        )

        for r in results:
            if r.user_id == user_id:
                return {
                    "score": r.score,
                    "breakdown": r.score_breakdown
                }

        return {"score": 0.0, "breakdown": {"reason": "no_match"}}

    # ===========================================================
    # MATCHING COMPLETO PARA UNA OFERTA
    # ===========================================================

    @classmethod
    def get_matching_workers_for_offer(
        cls,
        session: Session,
        job_offer_id: int,
        limit: int = 50
    ) -> List[MatchingWorkerResult]:

        offer: JobOffer | None = session.get(JobOffer, job_offer_id)
        if not offer or getattr(offer, "is_active", 1) == 0:
            return []

        # --------- datos oferta ----------
        required_skills = cls._parse_csv(
            getattr(offer, "required_skills", None)
            or getattr(offer, "requirements", None)
        )

        offer_location = cls._simple_location_norm(getattr(offer, "location", None))
        offer_region = cls._simple_location_norm(getattr(offer, "region", None))
        offer_comuna = cls._simple_location_norm(getattr(offer, "comuna", None))
        urgency = getattr(offer, "urgency", None)

        offer_salary = cls._parse_salary(getattr(offer, "salary_range", None))
        offer_availability = getattr(offer, "availability_json", None)

        # --------- perfiles worker ----------
        q = (
            select(UserProfile, AppUser)
            .join(AppUser, UserProfile.user_id == AppUser.id)
        )

        if hasattr(AppUser, "user_type"):
            q = q.where(AppUser.user_type == "worker")

        profiles = list(session.exec(q).all())
        if not profiles:
            return []

        # --------- certificados ----------
        certs_q = (
            select(
                UserCertificate.user_id,
                func.count(UserCertificate.id).label("certs_count")
            )
            .where(UserCertificate.is_active == 1)
            .group_by(UserCertificate.user_id)
        )
        certs_map = {uid: cnt for uid, cnt in session.exec(certs_q).all()}

        results: List[MatchingWorkerResult] = []

        # ===========================================================
        # LOOP PRINCIPAL DE MATCHING
        # ===========================================================
        for profile, user in profiles:
            breakdown: Dict[str, float] = {}

            # --------- skills ----------
            worker_skills = cls._parse_csv(getattr(profile, "skills", None))
            if required_skills:
                inter = set(worker_skills).intersection(required_skills)
                score = (len(inter) / len(required_skills)) * cls.W_SKILLS
            else:
                score = cls.W_SKILLS * 0.5

            breakdown["skills"] = round(score, 2)

            # --------- location ----------
            prof_region = cls._simple_location_norm(getattr(profile, "region", None))
            prof_comuna = cls._simple_location_norm(getattr(profile, "comuna", None))

            loc_score = 0.0
            if offer_comuna and prof_comuna and offer_comuna == prof_comuna:
                loc_score = cls.W_LOCATION
            elif offer_region and prof_region and offer_region == prof_region:
                loc_score = cls.W_LOCATION * 0.7
            elif offer_location and prof_comuna and offer_location in prof_comuna:
                loc_score = cls.W_LOCATION * 0.6
            elif offer_location and prof_region and offer_location in prof_region:
                loc_score = cls.W_LOCATION * 0.5
            else:
                loc_score = cls.W_LOCATION * 0.2

            breakdown["location"] = round(loc_score, 2)

            # --------- availability ----------
            prof_av = getattr(profile, "availability_json", None)
            if offer_availability and prof_av:
                av_score = cls.W_AVAILABILITY
            elif offer_availability and not prof_av:
                av_score = cls.W_AVAILABILITY * 0.3
            else:
                av_score = cls.W_AVAILABILITY * 0.6

            breakdown["availability"] = round(av_score, 2)

            # --------- rate ----------
            rate_hour = getattr(profile, "rate_hour", None)
            rate_score = cls.W_RATE * 0.6

            if rate_hour and offer_salary:
                # regla simple para no complicar
                if rate_hour * 8 <= offer_salary:
                    rate_score = cls.W_RATE
                else:
                    rate_score = cls.W_RATE * 0.4

            breakdown["rate"] = round(rate_score, 2)

            # --------- rating ----------
            rating_avg = getattr(profile, "rating_avg", None)
            reviews_count = getattr(profile, "reviews_count", 0)

            if rating_avg is None:
                rating_score = cls.W_RATING * 0.5
            else:
                base = min(max(float(rating_avg), 0), 5) / 5
                boost = min(reviews_count / 20, 1) * 0.2
                rating_score = cls.W_RATING * min(base + boost, 1)

            breakdown["rating"] = round(rating_score, 2)

            # --------- certificates ----------
            certs_count = certs_map.get(profile.user_id, 0)

            if certs_count >= 3:
                cert_score = cls.W_CERTS
            elif certs_count == 2:
                cert_score = cls.W_CERTS * 0.7
            elif certs_count == 1:
                cert_score = cls.W_CERTS * 0.4
            else:
                cert_score = cls.W_CERTS * 0.1

            breakdown["certificates"] = round(cert_score, 2)

            # --------- TOTAL SCORE ----------
            total = sum(breakdown.values())

            # Boost por urgencia + disponibilidad
            if urgency and str(urgency).upper() == "URGENT" and prof_av:
                total = min(total + 3, 100)

            # construir resultado final
            results.append(
                MatchingWorkerResult(
                    user_id=profile.user_id,
                    full_name=getattr(profile, "full_name", None) or getattr(user, "user", None),
                    avatar_url=getattr(profile, "avatar_url", None),
                    score=round(total, 2),
                    score_breakdown=breakdown,

                    skills=worker_skills,
                    years_experience=getattr(profile, "years_experience", None),
                    region=getattr(profile, "region", None),
                    comuna=getattr(profile, "comuna", None),
                    rate_hour=rate_hour,
                    min_shift_rate=getattr(profile, "min_shift_rate", None),

                    rating_avg=rating_avg,
                    reviews_count=reviews_count,
                    certificates_count=certs_count,

                    extra={}
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
