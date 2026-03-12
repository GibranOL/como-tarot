"""
Unit tests for the astrology service.

WHY: Zodiac sign and compatibility are surfaced prominently to users on their
profile and readings. A wrong sign (especially on cusp dates) would destroy
trust immediately.
"""
import pytest
from datetime import date

from app.services.astrology import (
    VALID_SIGNS,
    calculate_compatibility,
    get_sign_element,
    get_sign_info,
    get_zodiac_sign,
)


class TestZodiacSign:
    # (birth_date, expected_sign) — covers all 12 signs + cusp dates
    KNOWN_CASES = [
        (date(1990, 3, 21), "Aries"),
        (date(1990, 4, 19), "Aries"),
        (date(1990, 4, 20), "Taurus"),
        (date(1990, 5, 20), "Taurus"),
        (date(1990, 5, 21), "Gemini"),
        (date(1990, 6, 20), "Gemini"),
        (date(1990, 6, 21), "Cancer"),
        (date(1990, 7, 22), "Cancer"),
        (date(1990, 7, 23), "Leo"),
        (date(1990, 8, 22), "Leo"),
        (date(1990, 8, 23), "Virgo"),
        (date(1990, 9, 22), "Virgo"),
        (date(1990, 9, 23), "Libra"),
        (date(1990, 10, 22), "Libra"),
        (date(1990, 10, 23), "Scorpio"),
        (date(1990, 11, 21), "Scorpio"),
        (date(1990, 11, 22), "Sagittarius"),
        (date(1990, 12, 21), "Sagittarius"),
        (date(1990, 12, 22), "Capricorn"),
        (date(1990, 12, 31), "Capricorn"),
        (date(1990, 1, 1), "Capricorn"),
        (date(1990, 1, 19), "Capricorn"),
        (date(1990, 1, 20), "Aquarius"),
        (date(1990, 2, 18), "Aquarius"),
        (date(1990, 2, 19), "Pisces"),
        (date(1990, 3, 20), "Pisces"),
    ]

    def test_zodiac_sign_all_12_signs(self):
        """Verify get_zodiac_sign returns correct sign for all 12 signs."""
        for birth_date, expected in self.KNOWN_CASES:
            result = get_zodiac_sign(birth_date)
            assert result == expected, (
                f"Birth {birth_date}: expected {expected}, got {result}"
            )

    def test_zodiac_cusp_dates(self):
        """Cusp dates (day before and after each sign boundary) must resolve correctly."""
        # April 19 → Aries, April 20 → Taurus
        assert get_zodiac_sign(date(2000, 4, 19)) == "Aries"
        assert get_zodiac_sign(date(2000, 4, 20)) == "Taurus"
        # December 21 → Sagittarius, December 22 → Capricorn
        assert get_zodiac_sign(date(2000, 12, 21)) == "Sagittarius"
        assert get_zodiac_sign(date(2000, 12, 22)) == "Capricorn"

    def test_result_is_always_a_valid_sign(self):
        """get_zodiac_sign must always return a sign present in VALID_SIGNS."""
        for birth_date, _ in self.KNOWN_CASES:
            result = get_zodiac_sign(birth_date)
            assert result in VALID_SIGNS


class TestSignInfo:
    def test_all_12_signs_have_info(self):
        """get_sign_info must return a non-None dict for all 12 signs."""
        for sign in VALID_SIGNS:
            info = get_sign_info(sign)
            assert info is not None, f"Missing info for sign {sign}"

    def test_sign_info_has_required_fields(self):
        """Each sign's info dict must contain element, traits, and description."""
        required = ["element", "traits_en", "traits_es", "description_en", "description_es",
                    "compatible_signs", "ruling_planet"]
        for sign in VALID_SIGNS:
            info = get_sign_info(sign)
            for field in required:
                assert field in info, f"Sign {sign} missing field '{field}'"

    def test_element_is_one_of_four(self):
        """Every sign must belong to one of the four classical elements."""
        valid_elements = {"fire", "earth", "air", "water"}
        for sign in VALID_SIGNS:
            element = get_sign_element(sign)
            assert element in valid_elements, f"Sign {sign} has invalid element {element!r}"

    def test_three_signs_per_element(self):
        """Each element must have exactly 3 signs."""
        element_counts: dict[str, int] = {}
        for sign in VALID_SIGNS:
            elem = get_sign_element(sign)
            element_counts[elem] = element_counts.get(elem, 0) + 1
        for elem, count in element_counts.items():
            assert count == 3, f"Element {elem} has {count} signs, expected 3"


class TestCompatibility:
    def test_compatibility_score_is_in_range(self):
        """Compatibility score must always be between 1 and 100."""
        signs = list(VALID_SIGNS)
        for i in range(len(signs)):
            for j in range(i, len(signs)):
                result = calculate_compatibility(signs[i], signs[j])
                assert 1 <= result["score"] <= 100, (
                    f"{signs[i]}-{signs[j]} score {result['score']} out of range"
                )

    def test_same_sign_compatibility(self):
        """Same-sign compatibility must return a score (not crash) and be reasonably positive."""
        for sign in VALID_SIGNS:
            result = calculate_compatibility(sign, sign)
            assert 1 <= result["score"] <= 100
            assert result["level"] in ("excellent", "good", "moderate", "challenging")

    def test_known_compatible_pair_scores_high(self):
        """Aries and Leo are a well-known fire-fire compatible pair — score should be ≥ 80."""
        result = calculate_compatibility("Aries", "Leo")
        assert result["score"] >= 80, f"Expected high score, got {result['score']}"
        assert result["level"] == "excellent"

    def test_known_incompatible_pair_scores_low(self):
        """Aries and Cancer are traditionally challenging — score should be < 50."""
        result = calculate_compatibility("Aries", "Cancer")
        assert result["score"] < 50

    def test_result_has_required_keys(self):
        """Compatibility result must contain all expected keys."""
        result = calculate_compatibility("Taurus", "Virgo")
        required = ["score", "level", "element_a", "element_b", "description_en", "description_es"]
        for key in required:
            assert key in result, f"Missing key '{key}' in compatibility result"

    def test_invalid_sign_raises_value_error(self):
        """Passing an unknown sign name must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_compatibility("Aries", "Cthulhu")
        with pytest.raises(ValueError):
            calculate_compatibility("NotASign", "Leo")
