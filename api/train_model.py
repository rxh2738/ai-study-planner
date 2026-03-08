import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

MODEL_PATH = Path("study_model.joblib")


def train_from_rows(rows: list[dict]):
    if len(rows) < 3:
        raise ValueError("Need at least 3 training rows")

    X = []
    y = []

    for r in rows:
        X.append([
            r["minutes_spent"],
            r["days_until_deadline"] if r["days_until_deadline"] is not None else 999,
        ])
        y.append(r["hard_label"])

    X = np.array(X)
    y = np.array(y)

    model = LogisticRegression()
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    return {"ok": True, "saved_to": str(MODEL_PATH), "rows_used": len(rows)}