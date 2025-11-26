# app/schemas/admin_metrics.py

from sqlmodel import SQLModel


class AdminMetricsSummary(SQLModel):
    # Usuarios / cuentas
    total_users: int
    total_baristas: int
    total_cafes: int

    # Ofertas y asignaciones
    offers_total: int
    offers_published: int
    offers_with_applications: int
    assignments_total: int
    completed_shifts: int

    # Monetización
    gtv_total: int  # Gross Transaction Value: suma de gross_amount
    platform_earnings_from_cafes: int
    platform_earnings_from_baristas: int
    platform_earnings_total: int
    baristas_earnings_total: int  # suma de net_amount_barista

    take_rate: float  # platform_earnings_total / gtv_total (0..1)
