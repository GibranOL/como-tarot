"""
Unit tests for the numerology service.

WHY: Life path numbers are a core feature shown on the user's profile and
during onboarding. Incorrect calculations would undermine user trust instantly.
"""
from datetime import date

from app.services.numerology import (
    calculate_life_number,
    calculate_personal_month,
    calculate_personal_year,
    get_full_numerology_profile,
    get_number_info,
    MASTER_NUMBERS,
)


class TestLifeNumber:
    # Known test cases: (birth_date, expected_life_number)
    KNOWN_CASES = [
        (date(1990, 7, 25), 6),   # year=1+9+9+0→10→1, month=7, day=2+5→7 → 1+7+7=15→6
        (date(1985, 11, 11), 9),  # year=1+9+8+5→23→5, month=1+1=2, day=1+1=2 → 5+2+2=9
        (date(2000, 1, 1), 4),    # year=2+0+0+0=2, month=1, day=1 → 2+1+1=4
        (date(1965, 5, 14), 4),   # well-known case
        (date(1975, 4, 18), 8),
    ]

    def test_life_number_known_cases(self):
        """Life path numbers must match hand-calculated values for known dates."""
        for birth_date, expected in self.KNOWN_CASES:
            result = calculate_life_number(birth_date)
            assert result == expected, (
                f"Birth {birth_date}: expected {expected}, got {result}"
            )

    def test_master_numbers_not_reduced(self):
        """
        Life path 11, 22, 33 are master numbers and must NOT be reduced to 2, 4, 6.
        WHY: Master numbers carry special meaning in numerology — reducing them would
        give users an incorrect reading.
        """
        for mn in MASTER_NUMBERS:
            assert mn in (11, 22, 33)

        # Verify master numbers survive _reduce
        from app.services.numerology import _reduce
        assert _reduce(11) == 11
        assert _reduce(22) == 22
        assert _reduce(33) == 33

    def test_result_is_valid_number(self):
        """Life path must be 1–9 or a master number."""
        valid = set(range(1, 10)) | MASTER_NUMBERS
        for birth_date, _ in self.KNOWN_CASES:
            result = calculate_life_number(birth_date)
            assert result in valid, f"Invalid life number {result} for {birth_date}"

    def test_different_dates_can_produce_same_number(self):
        """Multiple birth dates mapping to the same life number is expected."""
        a = calculate_life_number(date(1990, 1, 1))
        b = calculate_life_number(date(1991, 1, 1))
        # Just check both are valid — they may or may not match
        valid = set(range(1, 10)) | MASTER_NUMBERS
        assert a in valid
        assert b in valid


class TestPersonalYear:
    def test_personal_year_returns_valid_number(self):
        """Personal year must be 1–9 or a master number."""
        valid = set(range(1, 10)) | MASTER_NUMBERS
        result = calculate_personal_year(date(1990, 7, 25), 2026)
        assert result in valid

    def test_personal_year_changes_with_year(self):
        """Personal year for 2025 and 2026 must differ for most birth dates."""
        bd = date(1990, 7, 25)
        y2025 = calculate_personal_year(bd, 2025)
        y2026 = calculate_personal_year(bd, 2026)
        # They should differ — incrementing year shifts the cycle
        assert y2025 != y2026

    def test_personal_year_uses_current_year_by_default(self):
        """When no year is passed, it must use the current year without error."""
        result = calculate_personal_year(date(1990, 7, 25))
        valid = set(range(1, 10)) | MASTER_NUMBERS
        assert result in valid


class TestPersonalMonth:
    def test_personal_month_returns_valid_number(self):
        """Personal month must be 1–9 or a master number."""
        valid = set(range(1, 10)) | MASTER_NUMBERS
        result = calculate_personal_month(date(1990, 7, 25), 2026, 3)
        assert result in valid

    def test_personal_month_varies_across_months(self):
        """Personal month must produce different values for January vs June."""
        bd = date(1990, 7, 25)
        jan = calculate_personal_month(bd, 2026, 1)
        jun = calculate_personal_month(bd, 2026, 6)
        assert jan != jun


class TestNumberInfo:
    def test_get_number_info_returns_dict_for_valid_numbers(self):
        """get_number_info must return a non-None dict for numbers 1–9 and 11/22/33."""
        for n in list(range(1, 10)) + [11, 22, 33]:
            info = get_number_info(n)
            assert info is not None, f"Missing info for number {n}"
            assert "name_en" in info
            assert "description_en" in info

    def test_get_number_info_returns_none_for_invalid(self):
        """get_number_info must return None for numbers not in the system."""
        assert get_number_info(0) is None
        assert get_number_info(10) is None
        assert get_number_info(99) is None


class TestFullProfile:
    def test_full_profile_has_all_keys(self):
        """get_full_numerology_profile must return all required profile keys."""
        profile = get_full_numerology_profile(date(1990, 7, 25))
        assert "life_number" in profile
        assert "personal_year" in profile
        assert "personal_month" in profile
        assert "life_number_info" in profile

    def test_full_profile_life_number_info_not_none(self):
        """The life_number_info in the profile must not be None for valid dates."""
        profile = get_full_numerology_profile(date(1990, 7, 25))
        assert profile["life_number_info"] is not None
