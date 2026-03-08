import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from models import Course, Topic, StudySession, SessionEvent

router = APIRouter(prefix="/dev", tags=["dev"])


def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id


def require_dev_mode() -> None:
    # Only allow in dev mode
    env = (os.getenv("ENV") or os.getenv("APP_ENV") or "dev").lower()
    if env not in {"dev", "development", "local"}:
        raise HTTPException(status_code=403, detail="Dev endpoints disabled")


@router.post("/reset")
def dev_reset(
    course_id: int = Query(..., description="Course id to wipe"),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    require_dev_mode()
    user_id = require_user_id(x_user_id)

    # Verify course belongs to this user
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.user_id == user_id)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 1) Find all sessions for this user+course
    session_ids = [
        s[0]
        for s in db.query(StudySession.id)
        .filter(StudySession.user_id == user_id, StudySession.course_id == course_id)
        .all()
    ]

    # 2) Delete child events first
    if session_ids:
        db.query(SessionEvent).filter(SessionEvent.session_id.in_(session_ids)).delete(
            synchronize_session=False
        )

    # 3) Delete sessions
    db.query(StudySession).filter(
        StudySession.user_id == user_id, StudySession.course_id == course_id
    ).delete(synchronize_session=False)

    # 4) Delete topics
    db.query(Topic).filter(
        Topic.user_id == user_id, Topic.course_id == course_id
    ).delete(synchronize_session=False)

    # 5) Delete the course itself
    db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).delete(
        synchronize_session=False
    )

    db.commit()

    return {"ok": True, "reset_course_id": course_id, "user_id": user_id}