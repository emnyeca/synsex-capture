from fractions import Fraction

from digitone_syx_toolkit.digitone2.length_codes import (
    explicit_length_code_to_sixteenth_units,
    find_exact_length_code_for_sixteenth_units,
)


def test_length_units_anchor_values():
    assert explicit_length_code_to_sixteenth_units(0x00) == Fraction(1, 8)
    assert explicit_length_code_to_sixteenth_units(0x02) == Fraction(1, 4)
    assert explicit_length_code_to_sixteenth_units(0x06) == Fraction(1, 2)
    assert explicit_length_code_to_sixteenth_units(0x0E) == Fraction(1, 1)
    assert explicit_length_code_to_sixteenth_units(0x1E) == Fraction(2, 1)
    assert explicit_length_code_to_sixteenth_units(0x2E) == Fraction(4, 1)
    assert explicit_length_code_to_sixteenth_units(0x3E) == Fraction(8, 1)
    assert explicit_length_code_to_sixteenth_units(0x4E) == Fraction(16, 1)
    assert explicit_length_code_to_sixteenth_units(0x5E) == Fraction(32, 1)
    assert explicit_length_code_to_sixteenth_units(0x6E) == Fraction(64, 1)
    assert explicit_length_code_to_sixteenth_units(0x7E) == Fraction(128, 1)


def test_find_exact_code_from_units_anchors():
    assert find_exact_length_code_for_sixteenth_units(Fraction(1, 8)) == 0x00
    assert find_exact_length_code_for_sixteenth_units(Fraction(1, 4)) == 0x02
    assert find_exact_length_code_for_sixteenth_units(Fraction(1, 2)) == 0x06
    assert find_exact_length_code_for_sixteenth_units(Fraction(1, 1)) == 0x0E
    assert find_exact_length_code_for_sixteenth_units(Fraction(2, 1)) == 0x1E
    assert find_exact_length_code_for_sixteenth_units(Fraction(4, 1)) == 0x2E
    assert find_exact_length_code_for_sixteenth_units(Fraction(8, 1)) == 0x3E
    assert find_exact_length_code_for_sixteenth_units(Fraction(16, 1)) == 0x4E
    assert find_exact_length_code_for_sixteenth_units(Fraction(128, 1)) == 0x7E
    assert find_exact_length_code_for_sixteenth_units(Fraction(3, 10)) is None
