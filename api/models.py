from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base
from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    topics = relationship("Topic", backref="course_obj", cascade="all, delete-orphan")

from sqlalchemy import Date  # add at top with other imports

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(160))
    deadline: Mapped["Date"] = mapped_column(Date, nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course")
    user = relationship("User")

class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)

    scheduled_for: Mapped["Date"] = mapped_column(Date, index=True)
    kind: Mapped[str] = mapped_column(String(20))  # "learn" or "review"
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic = relationship("Topic")


class SessionEvent(Base):
    __tablename__ = "session_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("study_sessions.id"), index=True)

    difficulty: Mapped[int] = mapped_column()  # 1-5
    minutes_spent: Mapped[int] = mapped_column()
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())