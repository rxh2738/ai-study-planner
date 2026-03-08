from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FEATURES_NUM = [
    "topic_attempts",
    "topic_avg_difficulty",
    "topic_last_difficulty",
    "days_since_topic_seen",
    "user_avg_difficulty_last_7",
    "user_avg_minutes_last_7",
    "days_until_deadline",
]

TARGET = "y_hard"


def time_split(rows: List[Dict[str, Any]], test_frac: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
    rows_sorted = sorted(
        rows,
        key=lambda r: (r.get("completed_at") or datetime.combine(r["scheduled_for"], datetime.min.time()))
    )
    n = len(rows_sorted)
    cut = max(1, int(n * (1 - test_frac)))
    return rows_sorted[:cut], rows_sorted[cut:]


def train_model(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(rows) < 10:
        return {"ok": False, "error": f"Need at least ~10 completed sessions to train. Got {len(rows)}."}

    train_rows, test_rows = time_split(rows, test_frac=0.2)

    def dicts_to_matrix(dicts: List[Dict[str, Any]]) -> np.ndarray:
        return np.array([[d.get(f, 0) for f in FEATURES_NUM] for d in dicts], dtype=float)

    X_train = dicts_to_matrix(train_rows)
    y_train = np.array([r[TARGET] for r in train_rows], dtype=int)

    X_test = dicts_to_matrix(test_rows)
    y_test = np.array([r[TARGET] for r in test_rows], dtype=int)

    pre = ColumnTransformer(
        transformers=[("num", StandardScaler(), list(range(len(FEATURES_NUM))))],
        remainder="drop",
    )

    clf = LogisticRegression(max_iter=200, class_weight="balanced")
    pipe = Pipeline([("pre", pre), ("clf", clf)])

    pipe.fit(X_train, y_train)
    probs = pipe.predict_proba(X_test)[:, 1]

    metrics = {
        "n_total": len(rows),
        "n_train": len(train_rows),
        "n_test": len(test_rows),
        "roc_auc": float(roc_auc_score(y_test, probs)) if len(set(y_test)) > 1 else None,
        "pr_auc": float(average_precision_score(y_test, probs)) if len(set(y_test)) > 1 else None,
        "brier": float(brier_score_loss(y_test, probs)),
        "positive_rate_test": float(y_test.mean()),
    }

    model_path = MODEL_DIR / "risk_logreg.joblib"
    joblib.dump(
        {"pipeline": pipe, "features": FEATURES_NUM, "trained_at": datetime.utcnow().isoformat(), "metrics": metrics},
        model_path,
    )

    return {"ok": True, "model_path": str(model_path), "metrics": metrics}