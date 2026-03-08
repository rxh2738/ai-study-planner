from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import Course, User
from schemas import CourseCreate, CourseOut

router = APIRouter()

def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id

@router.post("", response_model=CourseOut)
def create_course(
    payload: CourseCreate,
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)

    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()

    course = Course(user_id=user_id, name=payload.name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("", response_model=list[CourseOut])
def list_courses(
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)
    return (
        db.query(Course)
        .filter(Course.user_id == user_id)
        .order_by(Course.id.desc())
        .all()
    )