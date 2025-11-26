# app/controllers/admin_metrics_controller.py

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from sqlalchemy import func

from app.services.db.sql_server_connection import get_session

from app.models.user import AppUser
from app.models.job_offer import JobOffer
from app.models.job_application import JobApplication
from app.models.job_assignment import JobAssignment
from app.models.gig_payment import GigPayment
from app.schemas.admin_metrics import AdminMetricsSummary

router = APIRouter(prefix="/admin/metrics", tags=["AdminMetrics"])


@router.get("/summary", response_model=AdminMetricsSummary)
def get_admin_metrics_summary(
    # filtros opcionales por rango de fechas sobre los pagos (gig_payment.created_at)
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    session: Session = Depends(get_session),
):
    """
    Summary global para el dashboard admin.
    Aplica filtros de fecha sobre la tabla gig_payment (created_at).
    """

    # ------------------------
    # 1) Usuarios
    # ------------------------
    # Ajusta estos filtros de rol a lo que tengas en tu modelo AppUser
    total_users = session.exec(select(func.count(AppUser.id))).one()

    total_baristas = session.exec(
        select(func.count(AppUser.id)).where(AppUser.user_type == "barista")
    ).one()

    total_cafes = session.exec(
        select(func.count(AppUser.id)).where(AppUser.user_type == "cafe")
    ).one()

    # ------------------------
    # 2) Ofertas / Asignaciones
    # ------------------------
    offers_total = session.exec(select(func.count(JobOffer.id))).one()

    offers_published = session.exec(
        select(func.count(JobOffer.id)).where(JobOffer.status == "PUBLICADO")
    ).one()

    # Ofertas con al menos una postulación
    offers_with_applications = session.exec(
        select(func.count(func.distinct(JobApplication.job_offer_id)))
    ).one()

    assignments_total = session.exec(
        select(func.count(JobAssignment.id))
    ).one()

    completed_shifts = session.exec(
        select(func.count(JobAssignment.id)).where(JobAssignment.status == "COMPLETED")
    ).one()

    # ------------------------
    # 3) Monetización desde gig_payment
    # ------------------------
    gp_query = select(
        func.coalesce(func.sum(GigPayment.gross_amount), 0),
        func.coalesce(func.sum(GigPayment.fee_amount_cafe), 0),
        func.coalesce(func.sum(GigPayment.fee_amount_barista), 0),
        func.coalesce(func.sum(GigPayment.net_amount_barista), 0),
    )

    if date_from is not None:
        gp_query = gp_query.where(GigPayment.created_at >= date_from)
    if date_to is not None:
        gp_query = gp_query.where(GigPayment.created_at <= date_to)

    gtv_total, platform_from_cafes, platform_from_baristas, baristas_earnings_total = (
        session.exec(gp_query).one()
    )

    platform_earnings_total = platform_from_cafes + platform_from_baristas

    take_rate = (
        float(platform_earnings_total) / float(gtv_total)
        if gtv_total and gtv_total != 0
        else 0.0
    )

    return AdminMetricsSummary(
        total_users=total_users or 0,
        total_baristas=total_baristas or 0,
        total_cafes=total_cafes or 0,
        offers_total=offers_total or 0,
        offers_published=offers_published or 0,
        offers_with_applications=offers_with_applications or 0,
        assignments_total=assignments_total or 0,
        completed_shifts=completed_shifts or 0,
        gtv_total=int(gtv_total or 0),
        platform_earnings_from_cafes=int(platform_from_cafes or 0),
        platform_earnings_from_baristas=int(platform_from_baristas or 0),
        platform_earnings_total=int(platform_earnings_total or 0),
        baristas_earnings_total=int(baristas_earnings_total or 0),
        take_rate=take_rate,
    )
