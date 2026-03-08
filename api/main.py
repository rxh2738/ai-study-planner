from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import engine, Base
import models  # registers models with SQLAlchemy

from routers.courses import router as courses_router
from routers.topics import router as topics_router
from routers.schedule import router as schedule_router

from routers.sessions import router as sessions_router

from routes.ml import router as ml_router

from routers import dev
from routers import courses, topics, schedule, sessions, dashboard
from routers import ml

app = FastAPI(title="Study Coach API")

app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])



Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(ml.router, prefix="/ml", tags=["ml"])