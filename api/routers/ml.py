from pathlib import Path

import joblib
import numpy as np
from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from db import get_db
from models import StudySession, SessionEvent, Topic
from train_model import train_from_rows, MODEL_PATH

router = APIRouter()


def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return x_user_id


def build_rows(db: Session, user_id: str, course_id: int):
    events = (
        db.query(SessionEvent, StudySession, Topic)
        .join(StudySession, SessionEvent.session_id == StudySession.id)
        .join(Topic, StudySession.topic_id == Topic.id)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
        )
        .all()
    )

    rows = []
    for event, session, topic in events:
        days_until_deadline = None
        if topic.deadline:
            days_until_deadline = (topic.deadline - session.scheduled_for).days

        rows.append(
            {
                "session_id": session.id,
                "topic_id": topic.id,
                "topic_name": topic.name,
                "scheduled_for": str(session.scheduled_for),
                "difficulty": event.difficulty,
                "minutes_spent": event.minutes_spent,
                "days_until_deadline": days_until_deadline,
                "hard_label": 1 if event.difficulty >= 4 else 0,
            }
        )
    return rows


@router.get("/training_rows")
def training_rows(
    course_id: int = Query(...),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)
    rows = build_rows(db, user_id, course_id)
    return {"rows": rows, "count": len(rows)}


@router.post("/train")
def train_model_endpoint(
    course_id: int = Query(...),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user_id = require_user_id(x_user_id)
    rows = build_rows(db, user_id, course_id)

    result = train_from_rows(rows)
    return result


@router.get("/predict")
def predict_topic_difficulty(
    topic_id: int = Query(...),
    minutes_spent: int = Query(...),
    days_until_deadline: int = Query(...),
    x_user_id: str | None = Header(default=None),
):
    require_user_id(x_user_id)

    if not MODEL_PATH.exists():
        raise HTTPException(status_code=400, detail="Model not trained yet")

    model = joblib.load(MODEL_PATH)
    X = np.array([[minutes_spent, days_until_deadline]])
    prob = model.predict_proba(X)[0][1]

    return {
        "topic_id": topic_id,
        "hard_probability": float(prob),
        "suggestion": "Review sooner" if prob >= 0.5 else "Normal review spacing",
    }