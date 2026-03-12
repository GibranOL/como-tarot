"""
Numerology service — life path number, personal year/month, and meanings.
All logic is pure Python with no external dependencies (easy to test).
"""
import json
from datetime import date
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent / "data"

MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})


def _load_number_data() -> dict:
    path = _DATA_DIR / "life_numbers.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


_NUMBER_DATA: dict = _load_number_data()


def _reduce(n: int) -> int:
    """Reduce n to a single digit or preserve master numbers (11, 22, 33)."""
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def calculate_life_number(birth_date: date) -> int:
    """
    Pythagorean life-path number derived from the full birth date.

    Method: sum all digits of YYYY + MM + DD, then reduce.
    Master numbers 11, 22, 33 are preserved (not reduced further).

    Example: 1990-07-25
      year: 1+9+9+0 = 19  → 1+9 = 10 → 1+0 = 1
      month: 0+7 = 7
      day: 2+5 = 7
      total: 1 + 7 + 7 = 15 → 1+5 = 6
    """
    year_sum = _reduce(sum(int(d) for d in str(birth_date.year)))
    month_sum = _reduce(sum(int(d) for d in str(birth_date.month).zfill(2)))
    day_sum = _reduce(sum(int(d) for d in str(birth_date.day).zfill(2)))
    return _reduce(year_sum + month_sum + day_sum)


def calculate_personal_year(birth_date: date, target_year: int | None = None) -> int:
    """
    Personal year number for a given calendar year.

    Formula: reduce(birth_month + birth_day + target_year_digits)
    """
    year = target_year if target_year is not None else date.today().year
    month_sum = _reduce(sum(int(d) for d in str(birth_date.month).zfill(2)))
    day_sum = _reduce(sum(int(d) for d in str(birth_date.day).zfill(2)))
    year_sum = _reduce(sum(int(d) for d in str(year)))
    return _reduce(month_sum + day_sum + year_sum)


def calculate_personal_month(birth_date: date, target_year: int | None = None, target_month: int | None = None) -> int:
    """
    Personal month number for a given month in a given year.

    Formula: reduce(personal_year + current_month_number)
    """
    today = date.today()
    year = target_year if target_year is not None else today.year
    month = target_month if target_month is not None else today.month
    personal_year = calculate_personal_year(birth_date, year)
    return _reduce(personal_year + month)


def get_number_info(number: int) -> dict | None:
    """Return the meaning dict for a life path number, or None if not found."""
    return _NUMBER_DATA.get(str(number))


def get_full_numerology_profile(birth_date: date) -> dict:
    """
    Return the complete numerology profile for a user.

    Includes:
      - life_number
      - personal_year (current)
      - personal_month (current)
      - life_number_info (from data file)
    """
    life_number = calculate_life_number(birth_date)
    personal_year = calculate_personal_year(birth_date)
    personal_month = calculate_personal_month(birth_date)

    return {
        "life_number": life_number,
        "personal_year": personal_year,
        "personal_month": personal_month,
        "life_number_info": get_number_info(life_number),
    }
