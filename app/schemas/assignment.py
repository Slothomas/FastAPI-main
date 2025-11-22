from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.job_assignment import AssignmentStatus

class AssignmentCreate(BaseModel):
    job_offer_id: int
    worker_id: int
    client_id: int

class AssignmentUpdate(BaseModel):
    status: AssignmentStatus

class AssignmentResponse(BaseModel):
    id: int
    job_offer_id: int
    worker_id: int
    client_id: int
    status: AssignmentStatus
    assigned_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
