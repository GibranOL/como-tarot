import uuid
from typing import Any
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class TarotCard(SQLModel, table=True):
    __tablename__ = "tarot_cards"

    id: int = Field(primary_key=True)  # Using numeric ID (0-77) from deck
    name: str = Field(max_length=100, index=True)
    name_es: str = Field(max_length=100)
    arcana: str = Field(max_length=20)  # major | minor
    suit: str | None = Field(default=None, max_length=20, nullable=True)  # cups, wands, etc.
    
    # Metadata and meanings stored in JSON for flexibility
    # but still structured enough for the app
    meaning_upright_en: str
    meaning_upright_es: str
    meaning_reversed_en: str
    meaning_reversed_es: str
    
    keywords_en: list[str] = Field(sa_column=Column(JSON, nullable=False))
    keywords_es: list[str] = Field(sa_column=Column(JSON, nullable=False))
    
    image_path: str = Field(max_length=255)  # Local asset path in Flutter
