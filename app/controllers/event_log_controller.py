from fastapi import APIRouter, Depends, Query
from typing import List
from sqlmodel import Session

from app.services.db.sql_server_connection import get_session
from app.services.db.event_log_service import EventLogService
from app.schemas.event_log import EventLogCreate, EventLogResponse

router = APIRouter(prefix="/event-log", tags=["Event Log"])


@router.post("/", response_model=EventLogResponse)
def create_event(
    data: EventLogCreate,
    session: Session = Depends(get_session)
):
    ev = EventLogService.log_event(
        session=session,
        event_type=data.event_type,
        actor_id=data.actor_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        metadata=data.metadata
    )
    return EventLogResponse.from_model(ev)


@router.get("/entity", response_model=List[EventLogResponse])
def list_by_entity(
    entity_type: str = Query(...),
    entity_id: int = Query(..., gt=0),
    limit: int = Query(200, ge=1, le=500),
    session: Session = Depends(get_session)
):
    events = EventLogService.list_events_by_entity(session, entity_type, entity_id, limit)
    return [EventLogResponse.from_model(e) for e in events]


@router.get("/actor/{actor_id}", response_model=List[EventLogResponse])
def list_by_actor(
    actor_id: int,
    limit: int = Query(200, ge=1, le=500),
    session: Session = Depends(get_session)
):
    events = EventLogService.list_events_by_actor(session, actor_id, limit)
    return [EventLogResponse.from_model(e) for e in events]
