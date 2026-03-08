from pydantic import BaseModel, Field

class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)

class CourseOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

from datetime import date
from typing import Optional

class TopicCreate(BaseModel):
    course_id: int
    name: str = Field(min_length=1, max_length=160)
    deadline: Optional[date] = None

class TopicOut(BaseModel):
    id: int
    course_id: int
    name: str
    deadline: Optional[date] = None

    class Config:
        from_attributes = True

from datetime import date

class StudySessionOut(BaseModel):
    id: int
    course_id: int
    topic_id: int
    scheduled_for: date
    kind: str
    completed: bool

    class Config:
        from_attributes = True

class SessionCompleteIn(BaseModel):
    difficulty: int = Field(ge=1, le=5)
    minutes_spent: int = Field(ge=0, le=600)
    note: str | None = Field(default=None, max_length=500)