from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json


class EventLogCreate(BaseModel):
    event_type: str = Field(..., min_length=2, max_length=60)
    actor_id: Optional[int] = None
    entity_type: str = Field(..., min_length=2, max_length=60)
    entity_id: int = Field(..., gt=0)
    metadata: Optional[Dict[str, Any]] = None


class EventLogResponse(BaseModel):
    id: int
    event_type: str
    actor_id: Optional[int]
    entity_type: str
    entity_id: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, ev):
        meta_obj = None
        if ev.metadata:
            try:
                meta_obj = json.loads(ev.metadata)
            except:
                meta_obj = None

        return cls(
            id=ev.id,
            event_type=ev.event_type,
            actor_id=ev.actor_id,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            metadata=meta_obj,
            created_at=ev.created_at
        )
