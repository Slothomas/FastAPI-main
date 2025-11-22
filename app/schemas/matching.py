# app/schemas/matching.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MatchingWorkerResult(BaseModel):
    """
    Resultado de un trabajador recomendado para una oferta.
    """
    user_id: int
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    # score total 0-100
    score: float = Field(..., ge=0, le=100)

    # desglose para transparencia
    score_breakdown: Dict[str, float] = Field(default_factory=dict)

    # datos relevantes del perfil
    skills: List[str] = Field(default_factory=list)
    years_experience: Optional[int] = None
    region: Optional[str] = None
    comuna: Optional[str] = None
    rate_hour: Optional[float] = None
    min_shift_rate: Optional[float] = None
    rating_avg: Optional[float] = None
    reviews_count: int = 0
    certificates_count: int = 0

    # cualquier cosa extra útil para el front
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
