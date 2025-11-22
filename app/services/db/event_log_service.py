from datetime import datetime
from typing import Optional, Dict, Any, List
import json
from sqlmodel import Session, select

from app.models.event_log import EventLog


class EventLogService:

    @staticmethod
    def log_event(
        session: Session,
        event_type: str,
        entity_type: str,
        entity_id: int,
        actor_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventLog:
        ev = EventLog(
            event_type=event_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
        session.add(ev)
        session.commit()
        session.refresh(ev)
        return ev

    @staticmethod
    def list_events_by_entity(
        session: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 200
    ) -> List[EventLog]:
        q = (
            select(EventLog)
            .where(
                EventLog.entity_type == entity_type,
                EventLog.entity_id == entity_id
            )
            .order_by(EventLog.created_at.desc())
            .limit(limit)
        )
        return list(session.exec(q).all())

    @staticmethod
    def list_events_by_actor(
        session: Session,
        actor_id: int,
        limit: int = 200
    ) -> List[EventLog]:
        q = (
            select(EventLog)
            .where(EventLog.actor_id == actor_id)
            .order_by(EventLog.created_at.desc())
            .limit(limit)
        )
        return list(session.exec(q).all())
