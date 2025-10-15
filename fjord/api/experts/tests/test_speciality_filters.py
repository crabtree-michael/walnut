from experts.views import _parse_specialities
from experts.models import Speciality


def test_parse_specialities_accepts_valid_values():
    raw = [Speciality.WEIGHT_LOSS.value, "  ", Speciality.MUSCLE_HYPERTROPHY.value]
    selected, invalid = _parse_specialities(raw)

    assert invalid == []
    assert selected == [Speciality.WEIGHT_LOSS.value, Speciality.MUSCLE_HYPERTROPHY.value]


def test_parse_specialities_rejects_invalid_values():
    selected, invalid = _parse_specialities(["Invalid", "Also Bad"])

    assert selected == []
    assert invalid == ["Invalid", "Also Bad"]


def test_parse_specialities_supports_comma_separated_lists():
    raw = [
        f"{Speciality.WEIGHT_LOSS.value}, {Speciality.NUTRITION_COACHING.value}",
        Speciality.WEIGHT_LOSS.value,
    ]
    selected, invalid = _parse_specialities(raw)

    assert invalid == []
    assert selected == [
        Speciality.WEIGHT_LOSS.value,
        Speciality.NUTRITION_COACHING.value,
    ]
