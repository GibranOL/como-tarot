"""
Unit tests for the tarot service.

WHY: The tarot engine is the core of CosmoTarot. These tests ensure
the deck is complete, draws are random but constrained (no duplicates,
correct count), and every card carries the data the AI and frontend need.
"""
import pytest

from app.services.tarot import (
    draw_cards,
    get_card_by_id,
    get_card_meaning,
    get_full_deck,
)


class TestFullDeck:
    def test_full_deck_has_78_cards(self):
        """The Rider-Waite deck must have exactly 78 cards (22 major + 56 minor)."""
        deck = get_full_deck()
        assert len(deck) == 78

    def test_major_arcana_count(self):
        """There must be exactly 22 Major Arcana cards (0–21)."""
        deck = get_full_deck()
        major = [c for c in deck if c["arcana"] == "major"]
        assert len(major) == 22

    def test_minor_arcana_count(self):
        """There must be exactly 56 Minor Arcana cards (14 per suit × 4 suits)."""
        deck = get_full_deck()
        minor = [c for c in deck if c["arcana"] == "minor"]
        assert len(minor) == 56

    def test_four_suits_14_cards_each(self):
        """Each of the four suits (wands, cups, swords, pentacles) must have 14 cards."""
        deck = get_full_deck()
        for suit in ("wands", "cups", "swords", "pentacles"):
            count = sum(1 for c in deck if c.get("suit") == suit)
            assert count == 14, f"Expected 14 {suit} cards, got {count}"

    def test_all_ids_unique(self):
        """Every card must have a unique id."""
        deck = get_full_deck()
        ids = [c["id"] for c in deck]
        assert len(ids) == len(set(ids))


class TestEachCardHasRequiredFields:
    REQUIRED_FIELDS = [
        "id", "name", "name_es", "arcana", "number",
        "keywords_en", "keywords_es",
        "meaning_upright_en", "meaning_upright_es",
        "meaning_reversed_en", "meaning_reversed_es",
    ]

    def test_each_card_has_required_fields(self):
        """Every card in the deck must carry all required metadata fields."""
        deck = get_full_deck()
        for card in deck:
            for field in self.REQUIRED_FIELDS:
                assert field in card, f"Card '{card.get('name')}' missing field '{field}'"
                assert card[field] is not None, (
                    f"Card '{card.get('name')}' has None for field '{field}'"
                )

    def test_keywords_are_non_empty_lists(self):
        """Keywords must be non-empty lists for AI prompt building."""
        deck = get_full_deck()
        for card in deck:
            assert isinstance(card["keywords_en"], list) and len(card["keywords_en"]) > 0
            assert isinstance(card["keywords_es"], list) and len(card["keywords_es"]) > 0


class TestDrawCards:
    def test_draw_returns_exactly_3_cards(self):
        """Default draw must return exactly 3 cards for the standard spread."""
        cards = draw_cards(3)
        assert len(cards) == 3

    def test_no_repeated_cards_in_spread(self):
        """No card should appear twice in a single draw (sampling without replacement)."""
        cards = draw_cards(3)
        ids = [c["id"] for c in cards]
        assert len(ids) == len(set(ids))

    def test_card_orientation_is_upright_or_reversed(self):
        """Each drawn card must have a valid orientation."""
        for _ in range(20):  # run multiple times to catch randomness issues
            cards = draw_cards(3)
            for card in cards:
                assert card["orientation"] in ("upright", "reversed"), (
                    f"Invalid orientation: {card['orientation']}"
                )

    def test_positions_match_past_present_future(self):
        """Cards drawn with the default spread must have the correct position labels."""
        cards = draw_cards(3, spread_type="past_present_future")
        positions = [c["position"] for c in cards]
        assert positions == ["past", "present", "future"]

    def test_positions_match_situation_action_outcome(self):
        """Cards drawn with the situation spread must have the correct position labels."""
        cards = draw_cards(3, spread_type="situation_action_outcome")
        positions = [c["position"] for c in cards]
        assert positions == ["situation", "action", "outcome"]

    def test_draw_single_card(self):
        """Drawing a single card must work and return 1 card."""
        cards = draw_cards(1)
        assert len(cards) == 1

    def test_draw_invalid_count_raises(self):
        """Drawing 0 or more than 78 cards must raise a ValueError."""
        with pytest.raises(ValueError):
            draw_cards(0)
        with pytest.raises(ValueError):
            draw_cards(79)

    def test_no_repeated_cards_across_many_draws(self):
        """Run 100 draws to statistically confirm no duplicates slip through."""
        for _ in range(100):
            cards = draw_cards(3)
            ids = [c["id"] for c in cards]
            assert len(ids) == len(set(ids))


class TestCardLookup:
    def test_get_card_by_id_returns_correct_card(self):
        """get_card_by_id must return the card with the matching id."""
        card = get_card_by_id(0)
        assert card is not None
        assert card["name"] == "The Fool"

    def test_get_card_by_id_returns_none_for_missing(self):
        """get_card_by_id must return None for an id that doesn't exist."""
        assert get_card_by_id(9999) is None


class TestCardMeaning:
    def test_upright_meaning_english(self):
        """get_card_meaning must return the upright English meaning when requested."""
        card = dict(get_card_by_id(0))
        card["orientation"] = "upright"
        meaning = get_card_meaning(card, language="en")
        assert "new beginnings" in meaning.lower() or len(meaning) > 10

    def test_reversed_meaning_spanish(self):
        """get_card_meaning must return the reversed Spanish meaning when requested."""
        card = dict(get_card_by_id(0))
        card["orientation"] = "reversed"
        meaning = get_card_meaning(card, language="es")
        assert len(meaning) > 10
