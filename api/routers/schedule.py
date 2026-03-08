from datetime import date, timedelta

from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db import get_db, SessionLocal
from models import Course, Topic, StudySession, SessionEvent
from schemas import StudySessionOut

router = APIRouter()


def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id


def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


@router.post("/generate", response_model=list[StudySessionOut])
def generate_schedule(
    course_id: int = Query(...),
    days: int = Query(14),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)
    days = clamp(days, 1, 60)

    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.user_id == user_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    topics = (
        db.query(Topic)
        .filter(Topic.user_id == user_id, Topic.course_id == course_id)
        .all()
    )

    start = date.today()
    end = start + timedelta(days=days)

    base_offsets = [0, 1, 3, 7]

    # delete old sessions in this window, but child events first
    existing_sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
            StudySession.scheduled_for >= start,
            StudySession.scheduled_for <= end,
        )
        .all()
    )

    existing_ids = [s.id for s in existing_sessions]
    if existing_ids:
        db.query(SessionEvent).filter(
            SessionEvent.session_id.in_(existing_ids)
        ).delete(synchronize_session=False)

        db.query(StudySession).filter(
            StudySession.id.in_(existing_ids)
        ).delete(synchronize_session=False)

        db.commit()

    created: list[StudySession] = []

    for t in topics:
        extra_offsets: list[int] = []
        if t.deadline:
            days_to_deadline = (t.deadline - start).days
            if 0 <= days_to_deadline <= 7:
                extra_offsets = [2, 5]
            elif 8 <= days_to_deadline <= 14:
                extra_offsets = [4, 10]

        offsets = sorted(set(base_offsets + extra_offsets))

        for i, off in enumerate(offsets):
            d = start + timedelta(days=off)
            if d > end:
                continue

            kind = "learn" if i == 0 else "review"
            sess = StudySession(
                user_id=user_id,
                course_id=course_id,
                topic_id=t.id,
                scheduled_for=d,
                kind=kind,
                completed=False,
            )
            db.add(sess)
            created.append(sess)

    db.commit()

    for s in created:
        db.refresh(s)

    return created


@router.get("/today", response_model=list[StudySessionOut])
def today_queue(
    course_id: int = Query(...),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)
    today = date.today()

    sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
            StudySession.scheduled_for == today,
            StudySession.completed == False,
        )
        .order_by(StudySession.id.asc())
        .all()
    )
    return sessions


@router.get("/all")
def list_all_sessions(
    course_id: int = Query(...),
    x_user_id: str | None = Header(default=None),
):
    user_id = require_user_id(x_user_id)

    with SessionLocal() as db:
        sessions = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == user_id,
                StudySession.course_id == course_id,
            )
            .order_by(StudySession.scheduled_for.asc(), StudySession.id.asc())
            .all()
        )

        return [
            {
                "id": s.id,
                "course_id": s.course_id,
                "topic_id": s.topic_id,
                "scheduled_for": str(s.scheduled_for),
                "kind": s.kind,
                "completed": s.completed,
            }
            for s in sessions
        ]