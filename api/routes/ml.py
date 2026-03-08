from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

import joblib
import numpy as np
from fastapi import APIRouter, Header, HTTPException

from ml.train import MODEL_DIR, FEATURES_NUM, train_model

from db import SessionLocal
from models import StudySession, Topic

router = APIRouter()


def build_rows(db, user_id: str, course_id: int) -> List[Dict[str, Any]]:
    sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.course_id == course_id,
            StudySession.completed == True,
        )
        .all()
    )

    topics = (
        db.query(Topic)
        .filter(Topic.user_id == user_id, Topic.course_id == course_id)
        .all()
    )
    topic_by_id = {t.id: t for t in topics}

    # last 7 days user averages (fallback to scheduled_for if no completed_at)
    today = datetime.utcnow().date()
    cutoff = today - timedelta(days=7)

    recent = []
    for s in sessions:
        d = getattr(s, "completed_at", None)
        when = d.date() if d else s.scheduled_for
        if when >= cutoff:
            recent.append(s)

    user_avg_diff_last7 = float(np.mean([(getattr(s, "difficulty", 0) or 0) for s in recent])) if recent else 0.0
    user_avg_min_last7 = float(np.mean([(getattr(s, "minutes_spent", 0) or 0) for s in recent])) if recent else 0.0

    by_topic: Dict[int, List[StudySession]] = {}
    for s in sessions:
        by_topic.setdefault(s.topic_id, []).append(s)

    rows: List[Dict[str, Any]] = []

    for s in sessions:
        topic_hist = sorted(by_topic.get(s.topic_id, []), key=lambda x: x.scheduled_for)
        idx = topic_hist.index(s)
        prev = topic_hist[:idx]

        topic_attempts = len(prev)
        topic_avg_difficulty = float(np.mean([(getattr(x, "difficulty", 0) or 0) for x in prev])) if prev else 0.0
        topic_last_difficulty = float((getattr(prev[-1], "difficulty", 0) or 0)) if prev else 0.0

        last_seen = prev[-1].scheduled_for if prev else None
        days_since_topic_seen = int((s.scheduled_for - last_seen).days) if last_seen else 999

        topic = topic_by_id.get(s.topic_id)
        days_until_deadline = int((topic.deadline - s.scheduled_for).days) if (topic and topic.deadline) else 999

        diff = getattr(s, "difficulty", None)
        if diff is None:
            continue

        rows.append(
            {
                "topic_attempts": topic_attempts,
                "topic_avg_difficulty": topic_avg_difficulty,
                "topic_last_difficulty": topic_last_difficulty,
                "days_since_topic_seen": days_since_topic_seen,
                "user_avg_difficulty_last_7": user_avg_diff_last7,
                "user_avg_minutes_last_7": user_avg_min_last7,
                "days_until_deadline": days_until_deadline,
                "scheduled_for": s.scheduled_for,
                "completed_at": getattr(s, "completed_at", None),
                "y_hard": 1 if diff >= 4 else 0,
            }
        )

    return rows


@router.get("/ml/training_rows")
def ml_training_rows(course_id: int, x_user_id: str = Header(...)):
    with SessionLocal() as db:
        rows = build_rows(db, x_user_id, course_id)
    return {"n": len(rows), "sample": rows[:5]}


@router.post("/ml/train")
def ml_train(course_id: int, x_user_id: str = Header(...)):
    with SessionLocal() as db:
        rows = build_rows(db, x_user_id, course_id)

    out = train_model(rows)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error", "Training failed"))
    return out


@router.post("/ml/predict")
def ml_predict(course_id: int, topic_id: int, x_user_id: str = Header(...)):
    model_path = MODEL_DIR / "risk_logreg.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=400, detail="Model not trained yet. Run POST /ml/train first.")

    blob = joblib.load(model_path)
    pipe = blob["pipeline"]
    feats = blob["features"]

    with SessionLocal() as db:
        topic = (
            db.query(Topic)
            .filter(Topic.user_id == x_user_id, Topic.course_id == course_id, Topic.id == topic_id)
            .first()
        )
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        days_until_deadline = int((topic.deadline - datetime.utcnow().date()).days) if topic.deadline else 999

    x = {f: 0 for f in feats}
    x["days_until_deadline"] = days_until_deadline

    X = np.array([[x[f] for f in feats]], dtype=float)
    p = float(pipe.predict_proba(X)[0, 1])

    suggestion = (
        "Looks manageable — keep normal spacing."
        if p < 0.4
        else "This looks harder — do a short review tomorrow."
    )

    return {"risk_hard_prob": p, "suggestion": suggestion, "features_used": x, "trained_metrics": blob.get("metrics")}