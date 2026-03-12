import uuid
from datetime import date, datetime, timezone
from sqlmodel import Field, SQLModel


class CompatibilityReading(SQLModel, table=True):
    __tablename__ = "compatibility_readings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    partner_zodiac: str = Field(max_length=20)
    partner_birth_date: date | None = Field(default=None, nullable=True)
    ai_interpretation: str
    compatibility_score: int = Field(ge=1, le=100)
    language: str = Field(default="es", max_length=5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
