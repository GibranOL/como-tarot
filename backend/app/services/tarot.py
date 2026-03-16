"""
Tarot service — full 78-card Rider-Waite deck from Database.
Provides card drawing logic for 3-card spreads.
"""
import random
import logging
from typing import Literal
from sqlmodel import Session, select

from app.db.database import engine
from app.models.tarot import TarotCard

logger = logging.getLogger(__name__)

SpreadType = Literal["past_present_future", "situation_action_outcome"]

# Position labels per spread type
_SPREAD_POSITIONS: dict[SpreadType, list[str]] = {
    "past_present_future": ["past", "present", "future"],
    "situation_action_outcome": ["situation", "action", "outcome"],
}


def get_full_deck() -> list[TarotCard]:
    """Return the full 78-card deck from the database."""
    with Session(engine) as session:
        return session.exec(select(TarotCard)).all()


def draw_cards(
    n: int = 3,
    spread_type: SpreadType = "past_present_future",
) -> list[dict]:
    """
    Draw n unique cards from the database, each with an upright/reversed orientation
    and a positional label matching the spread type.

    Returns a list of card dicts enriched with:
      - orientation: "upright" | "reversed"
      - position: e.g. "past" | "present" | "future"
      - position_index: 0-based index in the spread
    """
    with Session(engine) as session:
        all_cards = session.exec(select(TarotCard)).all()
        
        if n < 1 or n > len(all_cards):
            raise ValueError(f"n must be between 1 and {len(all_cards)}, got {n}")

        selected = random.sample(all_cards, k=n)
        positions = _SPREAD_POSITIONS[spread_type]

        result = []
        for i, card in enumerate(selected):
            # Convert to dict for API response and enrich with session state
            card_dict = card.model_dump()
            card_dict["orientation"] = random.choice(["upright", "reversed"])
            card_dict["position"] = positions[i] if i < len(positions) else f"card_{i + 1}"
            card_dict["position_index"] = i
            result.append(card_dict)

        return result


def get_card_by_id(card_id: int) -> TarotCard | None:
    """Return a single card by its numeric id, or None if not found."""
    with Session(engine) as session:
        return session.get(TarotCard, card_id)


def get_card_meaning(card: dict | TarotCard, language: str = "es") -> str:
    """
    Return the human-readable meaning for a drawn card (includes orientation).
    `card` must have an 'orientation' key if it's a dict.
    """
    lang = language if language in ("es", "en") else "es"
    
    if isinstance(card, dict):
        orientation = card.get("orientation", "upright")
        if orientation == "upright":
            return card.get(f"meaning_upright_{lang}", "")
        return card.get(f"meaning_reversed_{lang}", "")
    
    # If it's a model instance, we need the orientation from somewhere else 
    # (this helper is mostly used with enriched dicts from draw_cards)
    return ""
