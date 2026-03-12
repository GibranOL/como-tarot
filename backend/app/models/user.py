import uuid
from datetime import date, time, datetime, timezone
from typing import Any
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=100)
    auth_provider: str = Field(default="email", max_length=20)  # google | apple | email

    # Astrological data
    birth_date: date
    birth_time: time | None = Field(default=None, nullable=True)
    birth_city: str | None = Field(default=None, max_length=100, nullable=True)
    birth_country: str | None = Field(default=None, max_length=100, nullable=True)
    latitude: float | None = Field(default=None, nullable=True)
    longitude: float | None = Field(default=None, nullable=True)

    # Calculated fields
    zodiac_sign: str | None = Field(default=None, max_length=20, nullable=True)
    life_number: int | None = Field(default=None, nullable=True)

    # Preferences (JSON)
    onboarding_answers: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    preferred_language: str = Field(default="es", max_length=5)
    timezone: str = Field(default="America/Mexico_City", max_length=50)

    # Subscription
    is_premium: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
