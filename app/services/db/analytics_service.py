from datetime import date, timedelta
from sqlmodel import Session, select, func

from app.models.job_offer import JobOffer, JobOfferStatus
from app.models.job_application import JobApplication
from app.models.job_assignment import JobAssignment, AssignmentStatus
from app.models.review import Review as JobReview  # modelo real app_review


# -----------------------------
# Helper rango de fechas
# -----------------------------
def _range(days: int):
    end = date.today()
    start = end - timedelta(days=days - 1)
    return start, end


# -----------------------------
# KPI GLOBAL
# -----------------------------
def get_overview(session: Session):

    # Ofertas
    total_offers = session.exec(select(func.count(JobOffer.id))).one()
    active_offers = session.exec(
        select(func.count(JobOffer.id)).where(
            JobOffer.status == JobOfferStatus.PUBLICADO
        )
    ).one()

    # Postulaciones
    total_applications = session.exec(
        select(func.count(JobApplication.id))
    ).one()

    applications_pending = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.status == "pending"
        )
    ).one()

    applications_accepted = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.status == "accepted"
        )
    ).one()

    applications_rejected = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.status == "rejected"
        )
    ).one()

    # Asignaciones
    total_assignments = session.exec(
        select(func.count(JobAssignment.id))
    ).one()

    assignments_active = session.exec(
        select(func.count(JobAssignment.id)).where(
            JobAssignment.status.in_([
                AssignmentStatus.ASSIGNED,
                AssignmentStatus.PENDING,
                AssignmentStatus.ACCEPTED
            ])
        )
    ).one()

    assignments_completed = session.exec(
        select(func.count(JobAssignment.id)).where(
            JobAssignment.status == AssignmentStatus.COMPLETED
        )
    ).one()

    # Reviews
    reviews_count = session.exec(
        select(func.count(JobReview.id)).where(
            JobReview.is_active == True
        )
    ).one()

    rating_avg = session.exec(
        select(func.avg(JobReview.rating)).where(
            JobReview.is_active == True
        )
    ).one()
    rating_avg = float(rating_avg) if rating_avg else None

    return {
        "total_offers": total_offers,
        "active_offers": active_offers,
        "total_applications": total_applications,
        "applications_pending": applications_pending,
        "applications_accepted": applications_accepted,
        "applications_rejected": applications_rejected,
        "total_assignments": total_assignments,
        "assignments_active": assignments_active,
        "assignments_completed": assignments_completed,
        "reviews_count": reviews_count,
        "rating_avg": rating_avg,
    }


# -----------------------------
# KPI POR CAFÉ (por usuario cafetería)
# cafe_user_id == JobOffer.created_by
# -----------------------------
def get_overview_by_cafe_user(session: Session, cafe_user_id: int):

    offers_q = select(JobOffer.id).where(
        JobOffer.created_by == cafe_user_id
    ).subquery()

    total_offers = session.exec(
        select(func.count(JobOffer.id)).where(
            JobOffer.created_by == cafe_user_id
        )
    ).one()

    active_offers = session.exec(
        select(func.count(JobOffer.id)).where(
            JobOffer.created_by == cafe_user_id,
            JobOffer.status == JobOfferStatus.PUBLICADO
        )
    ).one()

    total_applications = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_offer_id.in_(select(offers_q))
        )
    ).one()

    applications_pending = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_offer_id.in_(select(offers_q)),
            JobApplication.status == "pending"
        )
    ).one()

    applications_accepted = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_offer_id.in_(select(offers_q)),
            JobApplication.status == "accepted"
        )
    ).one()

    applications_rejected = session.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_offer_id.in_(select(offers_q)),
            JobApplication.status == "rejected"
        )
    ).one()

    total_assignments = session.exec(
        select(func.count(JobAssignment.id)).where(
            JobAssignment.job_offer_id.in_(select(offers_q))
        )
    ).one()

    assignments_active = session.exec(
        select(func.count(JobAssignment.id)).where(
            JobAssignment.job_offer_id.in_(select(offers_q)),
            JobAssignment.status.in_([
                AssignmentStatus.ASSIGNED,
                AssignmentStatus.PENDING,
                AssignmentStatus.ACCEPTED
            ])
        )
    ).one()

    assignments_completed = session.exec(
        select(func.count(JobAssignment.id)).where(
            JobAssignment.job_offer_id.in_(select(offers_q)),
            JobAssignment.status == AssignmentStatus.COMPLETED
        )
    ).one()

    reviews_count = session.exec(
        select(func.count(JobReview.id)).where(
            JobReview.job_offer_id.in_(select(offers_q)),
            JobReview.is_active == True
        )
    ).one()

    rating_avg = session.exec(
        select(func.avg(JobReview.rating)).where(
            JobReview.job_offer_id.in_(select(offers_q)),
            JobReview.is_active == True
        )
    ).one()

    return {
        "total_offers": total_offers,
        "active_offers": active_offers,
        "total_applications": total_applications,
        "applications_pending": applications_pending,
        "applications_accepted": applications_accepted,
        "applications_rejected": applications_rejected,
        "total_assignments": total_assignments,
        "assignments_active": assignments_active,
        "assignments_completed": assignments_completed,
        "reviews_count": reviews_count,
        "rating_avg": float(rating_avg) if rating_avg else None,
    }


# -----------------------------
# KPI POR BARISTA (worker)
# -----------------------------
def get_overview_by_barista(session: Session, user_id: int):

    total_applications = session.exec(
        select(func.count(JobApplication.id))
        .where(JobApplication.user_id == user_id)
    ).one()

    applications_pending = session.exec(
        select(func.count(JobApplication.id))
        .where(JobApplication.user_id == user_id,
               JobApplication.status == "pending")
    ).one()

    applications_accepted = session.exec(
        select(func.count(JobApplication.id))
        .where(JobApplication.user_id == user_id,
               JobApplication.status == "accepted")
    ).one()

    applications_rejected = session.exec(
        select(func.count(JobApplication.id))
        .where(JobApplication.user_id == user_id,
               JobApplication.status == "rejected")
    ).one()

    total_assignments = session.exec(
        select(func.count(JobAssignment.id))
        .where(JobAssignment.worker_id == user_id)
    ).one()

    assignments_active = session.exec(
        select(func.count(JobAssignment.id))
        .where(JobAssignment.worker_id == user_id,
               JobAssignment.status.in_([
                   AssignmentStatus.ASSIGNED,
                   AssignmentStatus.PENDING,
                   AssignmentStatus.ACCEPTED
               ]))
    ).one()

    assignments_completed = session.exec(
        select(func.count(JobAssignment.id))
        .where(JobAssignment.worker_id == user_id,
               JobAssignment.status == AssignmentStatus.COMPLETED)
    ).one()

    reviews_count = session.exec(
        select(func.count(JobReview.id))
        .where(JobReview.reviewee_id == user_id,
               JobReview.is_active == True)
    ).one()

    rating_avg = session.exec(
        select(func.avg(JobReview.rating))
        .where(JobReview.reviewee_id == user_id,
               JobReview.is_active == True)
    ).one()
    rating_avg = float(rating_avg) if rating_avg else None

    return {
        "total_offers": 0,
        "active_offers": 0,
        "total_applications": total_applications,
        "applications_pending": applications_pending,
        "applications_accepted": applications_accepted,
        "applications_rejected": applications_rejected,
        "total_assignments": total_assignments,
        "assignments_active": assignments_active,
        "assignments_completed": assignments_completed,
        "reviews_count": reviews_count,
        "rating_avg": rating_avg,
    }


# -----------------------------
# TIMESERIES: APPLICATIONS / DAY
# filtros: cafe_user_id (created_by) y/o barista_id
# -----------------------------
def get_timeseries_applications(session: Session, days: int = 30,
                                cafe_user_id: int | None = None,
                                barista_id: int | None = None):

    start, _ = _range(days)

    q = select(
        func.cast(JobApplication.applied_at, date).label("d"),
        func.count(JobApplication.id).label("c"),
    ).where(JobApplication.applied_at >= start)

    if barista_id is not None:
        q = q.where(JobApplication.user_id == barista_id)

    if cafe_user_id is not None:
        offers_q = select(JobOffer.id).where(JobOffer.created_by == cafe_user_id)
        q = q.where(JobApplication.job_offer_id.in_(offers_q))

    q = q.group_by("d").order_by("d")

    rows = session.exec(q).all()
    return [{"date": r.d.isoformat(), "value": r.c} for r in rows]


# -----------------------------
# TIMESERIES: ASSIGNMENTS / DAY
# -----------------------------
def get_timeseries_assignments(session: Session, days: int = 30,
                               cafe_user_id: int | None = None,
                               barista_id: int | None = None):

    start, _ = _range(days)

    q = select(
        func.cast(JobAssignment.assigned_at, date).label("d"),
        func.count(JobAssignment.id).label("c"),
    ).where(JobAssignment.assigned_at >= start)

    if barista_id is not None:
        q = q.where(JobAssignment.worker_id == barista_id)

    if cafe_user_id is not None:
        offers_q = select(JobOffer.id).where(JobOffer.created_by == cafe_user_id)
        q = q.where(JobAssignment.job_offer_id.in_(offers_q))

    q = q.group_by("d").order_by("d")

    rows = session.exec(q).all()
    return [{"date": r.d.isoformat(), "value": r.c} for r in rows]


# -----------------------------
# TIMESERIES: REVIEWS / DAY
# -----------------------------
def get_timeseries_reviews(session: Session, days: int = 30,
                           cafe_user_id: int | None = None,
                           barista_id: int | None = None):

    start, _ = _range(days)

    q = select(
        func.cast(JobReview.created_at, date).label("d"),
        func.count(JobReview.id).label("c"),
    ).where(
        JobReview.created_at >= start,
        JobReview.is_active == True
    )

    if barista_id is not None:
        q = q.where(JobReview.reviewee_id == barista_id)

    if cafe_user_id is not None:
        offers_q = select(JobOffer.id).where(JobOffer.created_by == cafe_user_id)
        q = q.where(JobReview.job_offer_id.in_(offers_q))

    q = q.group_by("d").order_by("d")

    rows = session.exec(q).all()
    return [{"date": r.d.isoformat(), "value": r.c} for r in rows]


# -----------------------------
# FUNNEL COMPLETO
# filtros: cafe_user_id (created_by) y/o barista_id
# -----------------------------
def get_funnel(session: Session, days: int = 30,
               cafe_user_id: int | None = None,
               barista_id: int | None = None):

    start, _ = _range(days)

    offers_q = select(JobOffer.id).where(JobOffer.created_at >= start)

    if cafe_user_id is not None:
        offers_q = offers_q.where(JobOffer.created_by == cafe_user_id)

    # 1) Offers del rango
    offers_count = session.exec(
        select(func.count(JobOffer.id)).where(
            JobOffer.created_at >= start,
            JobOffer.created_by == cafe_user_id
        )
        if cafe_user_id is not None
        else select(func.count(JobOffer.id)).where(JobOffer.created_at >= start)
    ).one()

    # 2) Applications del rango
    apps_q = select(JobApplication.id).where(
        JobApplication.applied_at >= start,
        JobApplication.job_offer_id.in_(offers_q)
    )
    if barista_id is not None:
        apps_q = apps_q.where(JobApplication.user_id == barista_id)

    applications_count = session.exec(
        select(func.count()).select_from(apps_q.subquery())
    ).one()

    # 3) Accepted
    accepted_q = apps_q.where(JobApplication.status == "accepted")
    accepted_count = session.exec(
        select(func.count()).select_from(accepted_q.subquery())
    ).one()

    # 4) Assignments del rango
    assign_q = select(JobAssignment.id).where(
        JobAssignment.assigned_at >= start,
        JobAssignment.job_offer_id.in_(offers_q)
    )
    if barista_id is not None:
        assign_q = assign_q.where(JobAssignment.worker_id == barista_id)

    assignments_count = session.exec(
        select(func.count()).select_from(assign_q.subquery())
    ).one()

    # 5) Completed
    completed_q = assign_q.where(JobAssignment.status == AssignmentStatus.COMPLETED)
    completed_count = session.exec(
        select(func.count()).select_from(completed_q.subquery())
    ).one()

    # 6) Reviews del rango
    reviews_q = select(JobReview.id).where(
        JobReview.created_at >= start,
        JobReview.is_active == True,
        JobReview.job_offer_id.in_(offers_q)
    )
    if barista_id is not None:
        reviews_q = reviews_q.where(JobReview.reviewee_id == barista_id)

    reviews_count = session.exec(
        select(func.count()).select_from(reviews_q.subquery())
    ).one()

    return [
        {"step": "offers", "count": offers_count},
        {"step": "applications", "count": applications_count},
        {"step": "accepted", "count": accepted_count},
        {"step": "assignments", "count": assignments_count},
        {"step": "completed", "count": completed_count},
        {"step": "reviews", "count": reviews_count},
    ]


# -----------------------------
# TOP BARISTAS (global)
# -----------------------------
def get_top_baristas(session: Session, limit: int = 5, min_reviews: int = 2):

    q = select(
        JobReview.reviewee_id,
        func.avg(JobReview.rating).label("avg_rating"),
        func.count(JobReview.id).label("reviews_count")
    ).where(
        JobReview.is_active == True
    ).group_by(
        JobReview.reviewee_id
    ).having(
        func.count(JobReview.id) >= min_reviews
    ).order_by(
        func.avg(JobReview.rating).desc()
    ).limit(limit)

    rows = session.exec(q).all()

    return [
        {
            "id": reviewee_id,
            "name": f"User {reviewee_id}",
            "value": float(avg_rating),
            "reviews_count": reviews_count
        }
        for reviewee_id, avg_rating, reviews_count in rows
    ]


# -----------------------------
# TOP CAFÉS (global) por usuario creador
# NO usa business_id
# -----------------------------
def get_top_businesses(session: Session, limit: int = 5, min_reviews: int = 2):

    # agrupamos por el usuario cafetería (created_by) de la oferta
    q = select(
        JobOffer.created_by.label("cafe_user_id"),
        func.avg(JobReview.rating).label("avg_rating"),
        func.count(JobReview.id).label("reviews_count"),
        func.max(JobOffer.company).label("company_name")
    ).join(
        JobReview, JobReview.job_offer_id == JobOffer.id
    ).where(
        JobReview.is_active == True
    ).group_by(
        JobOffer.created_by
    ).having(
        func.count(JobReview.id) >= min_reviews
    ).order_by(
        func.avg(JobReview.rating).desc()
    ).limit(limit)

    rows = session.exec(q).all()

    return [
        {
            "id": r.cafe_user_id,
            "name": r.company_name or f"Café {r.cafe_user_id}",
            "value": float(r.avg_rating),
            "reviews_count": r.reviews_count
        }
        for r in rows
    ]


# -----------------------------
# RANKING INTERNO CAFÉ:
# top baristas que trabajaron en mis ofertas
# -----------------------------
def get_top_baristas_by_cafe_user(session: Session,
                                  cafe_user_id: int,
                                  limit: int = 5,
                                  min_reviews: int = 1):

    offers_q = select(JobOffer.id).where(
        JobOffer.created_by == cafe_user_id
    )

    q = select(
        JobReview.reviewee_id,
        func.avg(JobReview.rating).label("avg_rating"),
        func.count(JobReview.id).label("reviews_count")
    ).where(
        JobReview.is_active == True,
        JobReview.job_offer_id.in_(offers_q)
    ).group_by(
        JobReview.reviewee_id
    ).having(
        func.count(JobReview.id) >= min_reviews
    ).order_by(
        func.avg(JobReview.rating).desc()
    ).limit(limit)

    rows = session.exec(q).all()

    return [
        {
            "id": reviewee_id,
            "name": f"User {reviewee_id}",
            "value": float(avg_rating),
            "reviews_count": reviews_count
        }
        for reviewee_id, avg_rating, reviews_count in rows
    ]
