from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from db import get_db
from models import StudySession, SessionEvent

router = APIRouter()


def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id


@router.get("/summary")
def dashboard_summary(
    course_id: int = Query(...),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)

    total_sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
        )
        .count()
    )

    completed_sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
            StudySession.completed == True,
        )
        .count()
    )

    upcoming_sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
            StudySession.completed == False,
        )
        .count()
    )

    events = (
        db.query(SessionEvent)
        .join(StudySession, SessionEvent.session_id == StudySession.id)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
        )
        .all()
    )

    total_minutes = sum(e.minutes_spent for e in events) if events else 0
    avg_difficulty = (
        round(sum(e.difficulty for e in events) / len(events), 2)
        if events
        else None
    )

    completion_rate = (
        round(completed_sessions / total_sessions, 2) if total_sessions > 0 else 0
    )

    return {
        "course_id": course_id,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "upcoming_sessions": upcoming_sessions,
        "total_minutes": total_minutes,
        "avg_difficulty": avg_difficulty,
        "completion_rate": completion_rate,
    }