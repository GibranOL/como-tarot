import uuid
from datetime import date, datetime, timezone
from typing import Any
from sqlmodel import Field, SQLModel, Column, UniqueConstraint
from sqlalchemy import JSON


class DailyReading(SQLModel, table=True):
    __tablename__ = "daily_readings"
    __table_args__ = (
        UniqueConstraint("user_id", "reading_date", name="uq_daily_reading_per_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    reading_date: date
    cards_drawn: list[Any] = Field(sa_column=Column(JSON, nullable=False))
    ai_interpretation: str
    spread_type: str = Field(default="past_present_future", max_length=50)
    language: str = Field(default="es", max_length=5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TarotistQuestion(SQLModel, table=True):
    __tablename__ = "tarotist_questions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    question: str
    answer: str
    category: str = Field(default="personal", max_length=20)  # love | career | personal | spiritual
    is_free: bool = Field(default=True)
    language: str = Field(default="es", max_length=5)
    asked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
