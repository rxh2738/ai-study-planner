from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db import get_db
from models import Topic, Course, User
from schemas import TopicCreate, TopicOut

router = APIRouter()

def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id

@router.post("", response_model=TopicOut)
def create_topic(
    payload: TopicCreate,
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)

    # Ensure user exists
    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()

    # Verify course belongs to user
    course = db.query(Course).filter(Course.id == payload.course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    topic = Topic(
        user_id=user_id,
        course_id=payload.course_id,
        name=payload.name,
        deadline=payload.deadline,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic

@router.get("", response_model=list[TopicOut])
def list_topics(
    course_id: int = Query(...),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)

    topics = (
        db.query(Topic)
        .filter(Topic.user_id == user_id, Topic.course_id == course_id)
        .order_by(Topic.id.desc())
        .all()
    )
    return topics