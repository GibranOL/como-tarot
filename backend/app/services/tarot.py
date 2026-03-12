"""
Tarot service — full 78-card Rider-Waite deck with bilingual meanings.
Provides card drawing logic for 3-card spreads.
"""
import json
import random
from pathlib import Path
from typing import Literal

_DATA_DIR = Path(__file__).parent.parent / "data"

SpreadType = Literal["past_present_future", "situation_action_outcome"]

# Position labels per spread type
_SPREAD_POSITIONS: dict[SpreadType, list[str]] = {
    "past_present_future": ["past", "present", "future"],
    "situation_action_outcome": ["situation", "action", "outcome"],
}


def _load_deck() -> list[dict]:
    """Load the full 78-card deck from JSON (lazy, cached at module level)."""
    path = _DATA_DIR / "tarot_deck.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# Module-level cache — loaded once on first import.
_DECK: list[dict] = _load_deck()


def get_full_deck() -> list[dict]:
    """Return the full 78-card deck."""
    return _DECK


def draw_cards(
    n: int = 3,
    spread_type: SpreadType = "past_present_future",
) -> list[dict]:
    """
    Draw n unique cards from the deck, each with an upright/reversed orientation
    and a positional label matching the spread type.

    Returns a list of card dicts enriched with:
      - orientation: "upright" | "reversed"
      - position: e.g. "past" | "present" | "future"
      - position_index: 0-based index in the spread
    """
    if n < 1 or n > len(_DECK):
        raise ValueError(f"n must be between 1 and {len(_DECK)}, got {n}")

    selected = random.sample(_DECK, k=n)
    positions = _SPREAD_POSITIONS[spread_type]

    result = []
    for i, card in enumerate(selected):
        enriched = dict(card)  # shallow copy so we don't mutate the cached deck
        enriched["orientation"] = random.choice(["upright", "reversed"])
        enriched["position"] = positions[i] if i < len(positions) else f"card_{i + 1}"
        enriched["position_index"] = i
        result.append(enriched)

    return result


def get_card_by_id(card_id: int) -> dict | None:
    """Return a single card by its numeric id, or None if not found."""
    for card in _DECK:
        if card["id"] == card_id:
            return card
    return None


def get_card_meaning(card: dict, language: str = "es") -> str:
    """
    Return the human-readable meaning for a drawn card (includes orientation).
    `card` must have an 'orientation' key (as returned by draw_cards).
    """
    orientation = card.get("orientation", "upright")
    lang = language if language in ("es", "en") else "es"

    if orientation == "upright":
        return card.get(f"meaning_upright_{lang}", card.get("meaning_upright_en", ""))
    return card.get(f"meaning_reversed_{lang}", card.get("meaning_reversed_en", ""))
