from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import json


class NotificationCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    type: str = Field(..., min_length=2, max_length=50)
    payload: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    payload: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, notif):
        payload_obj = None
        if notif.payload:
            try:
                payload_obj = json.loads(notif.payload)
            except:
                payload_obj = None

        return cls(
            id=notif.id,
            user_id=notif.user_id,
            type=notif.type,
            payload=payload_obj,
            is_read=notif.is_read,
            created_at=notif.created_at
        )


class NotificationMarkRead(BaseModel):
    is_read: bool = True
