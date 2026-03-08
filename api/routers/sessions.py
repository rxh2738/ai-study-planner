from datetime import timedelta

from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import StudySession, SessionEvent
from schemas import SessionCompleteIn

router = APIRouter()


def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id


@router.post("/{session_id}/complete")
def complete_session(
    session_id: int,
    payload: SessionCompleteIn,
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)

    sess = (
        db.query(StudySession)
        .filter(StudySession.id == session_id, StudySession.user_id == user_id)
        .first()
    )
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    sess.completed = True

    event = SessionEvent(
        user_id=user_id,
        session_id=session_id,
        difficulty=payload.difficulty,
        minutes_spent=payload.minutes_spent,
        note=payload.note,
    )
    db.add(event)

    # adaptive next review rule
    if payload.difficulty >= 4:
        next_days = 1
    elif payload.difficulty == 3:
        next_days = 3
    else:
        next_days = 5

    next_date = sess.scheduled_for + timedelta(days=next_days)

    next_session = StudySession(
        user_id=sess.user_id,
        course_id=sess.course_id,
        topic_id=sess.topic_id,
        scheduled_for=next_date,
        kind="review",
        completed=False,
    )
    db.add(next_session)

    db.commit()
    db.refresh(next_session)

    return {
        "ok": True,
        "completed_session_id": sess.id,
        "next_session_id": next_session.id,
        "next_review_date": str(next_session.scheduled_for),
    }