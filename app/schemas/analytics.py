from typing import Optional, List
from sqlmodel import SQLModel


class OverviewKPI(SQLModel):
    total_offers: int
    active_offers: int

    total_applications: int
    applications_pending: int
    applications_accepted: int
    applications_rejected: int

    total_assignments: int
    assignments_active: int
    assignments_completed: int

    reviews_count: int
    rating_avg: Optional[float] = None


class TimePoint(SQLModel):
    date: str
    value: int


class TimeSeries(SQLModel):
    metric: str
    points: List[TimePoint]


class FunnelStep(SQLModel):
    step: str
    count: int


class Funnel(SQLModel):
    steps: List[FunnelStep]


class RankingItem(SQLModel):
    id: int
    name: str
    value: float


class Rankings(SQLModel):
    metric: str
    items: List[RankingItem]
