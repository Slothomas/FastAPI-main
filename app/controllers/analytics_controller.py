from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.services.db.sql_server_connection import get_session
from app.schemas.analytics import OverviewKPI, TimeSeries, Funnel, Rankings
from app.services.db.analytics_service import (
    get_overview,
    get_overview_by_cafe_user,
    get_overview_by_barista,
    get_timeseries_applications,
    get_timeseries_assignments,
    get_timeseries_reviews,
    get_funnel,
    get_top_baristas,
    get_top_businesses,
    get_top_baristas_by_cafe_user
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# -----------------------------
# OVERVIEWS GLOBAL / CAFÉ / BARISTA
# -----------------------------
@router.get("/overview", response_model=OverviewKPI)
def overview(session: Session = Depends(get_session)):
    return get_overview(session)


@router.get("/cafe/{cafe_user_id}/overview", response_model=OverviewKPI)
def cafe_overview(cafe_user_id: int, session: Session = Depends(get_session)):
    return get_overview_by_cafe_user(session, cafe_user_id)


@router.get("/barista/{user_id}/overview", response_model=OverviewKPI)
def barista_overview(user_id: int, session: Session = Depends(get_session)):
    return get_overview_by_barista(session, user_id)


# -----------------------------
# TIMESERIES (applications, assignments, reviews)
# -----------------------------
@router.get("/timeseries/applications", response_model=TimeSeries)
def ts_applications(
    days: int = 30,
    cafe_user_id: int | None = None,
    barista_id: int | None = None,
    session: Session = Depends(get_session)
):
    points = get_timeseries_applications(session, days, cafe_user_id, barista_id)
    return {"metric": "applications", "points": points}


@router.get("/timeseries/assignments", response_model=TimeSeries)
def ts_assignments(
    days: int = 30,
    cafe_user_id: int | None = None,
    barista_id: int | None = None,
    session: Session = Depends(get_session)
):
    points = get_timeseries_assignments(session, days, cafe_user_id, barista_id)
    return {"metric": "assignments", "points": points}


@router.get("/timeseries/reviews", response_model=TimeSeries)
def ts_reviews(
    days: int = 30,
    cafe_user_id: int | None = None,
    barista_id: int | None = None,
    session: Session = Depends(get_session)
):
    points = get_timeseries_reviews(session, days, cafe_user_id, barista_id)
    return {"metric": "reviews", "points": points}


# -----------------------------
# FUNNEL COMPLETO
# -----------------------------
@router.get("/funnel", response_model=Funnel)
def funnel(
    days: int = 30,
    cafe_user_id: int | None = None,
    barista_id: int | None = None,
    session: Session = Depends(get_session)
):
    steps = get_funnel(session, days, cafe_user_id, barista_id)
    return {"steps": steps}


# -----------------------------
# RANKINGS GENERALES
# -----------------------------
@router.get("/rankings/top-baristas", response_model=Rankings)
def rankings_top_baristas(
    limit: int = 5,
    min_reviews: int = 2,
    session: Session = Depends(get_session)
):
    items = get_top_baristas(session, limit, min_reviews)
    return {"metric": "rating", "items": items}


@router.get("/rankings/top-cafes", response_model=Rankings)
def rankings_top_businesses(
    limit: int = 5,
    min_reviews: int = 2,
    session: Session = Depends(get_session)
):
    items = get_top_businesses(session, limit, min_reviews)
    return {"metric": "rating", "items": items}


# -----------------------------
# RANKING INTERNO POR CAFÉ (POR USUARIO CREADOR)
# -----------------------------
@router.get("/cafe/{cafe_user_id}/rankings/top-baristas", response_model=Rankings)
def cafe_rankings_top_baristas(
    cafe_user_id: int,
    limit: int = 5,
    min_reviews: int = 1,
    session: Session = Depends(get_session)
):
    items = get_top_baristas_by_cafe_user(session, cafe_user_id, limit, min_reviews)
    return {"metric": "rating", "items": items}
