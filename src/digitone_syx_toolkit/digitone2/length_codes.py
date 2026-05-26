"""Length code tables and helpers for Digitone II trigger encoding."""

from __future__ import annotations

from fractions import Fraction

EXPLICIT_LENGTH_CODE_TO_DISPLAY = {
    0x00: ".125",
    0x01: ".188",
    0x02: "1/64",
    0x03: ".313",
    0x04: ".375",
    0x05: ".438",
    0x06: "1/32",
    0x07: ".563",
    0x08: ".625",
    0x09: ".688",
    0x0A: ".750",
    0x0B: ".813",
    0x0C: ".875",
    0x0D: ".938",
    0x0E: "1/16",
    0x0F: "1.06",
    0x10: "1.13",
    0x11: "1.19",
    0x12: "1.25",
    0x13: "1.31",
    0x14: "1.38",
    0x15: "1.44",
    0x16: "1.50",
    0x17: "1.56",
    0x18: "1.63",
    0x19: "1.69",
    0x1A: "1.75",
    0x1B: "1.81",
    0x1C: "1.88",
    0x1D: "1.94",
    0x1E: "1/8",
    0x1F: "2.13",
    0x20: "2.25",
    0x21: "2.38",
    0x22: "2.50",
    0x23: "2.63",
    0x24: "2.75",
    0x25: "2.88",
    0x26: "3.00",
    0x27: "3.13",
    0x28: "3.25",
    0x29: "3.38",
    0x2A: "3.50",
    0x2B: "3.63",
    0x2C: "3.75",
    0x2D: "3.88",
    0x2E: "1/4",
    0x2F: "4.25",
    0x30: "4.50",
    0x31: "4.75",
    0x32: "5.00",
    0x33: "5.25",
    0x34: "5.50",
    0x35: "5.75",
    0x36: "6.00",
    0x37: "6.25",
    0x38: "6.50",
    0x39: "6.75",
    0x3A: "7.00",
    0x3B: "7.25",
    0x3C: "7.50",
    0x3D: "7.75",
    0x3E: "1/2",
    0x3F: "8.50",
    0x40: "9.00",
    0x41: "9.50",
    0x42: "10.0",
    0x43: "10.5",
    0x44: "11.0",
    0x45: "11.5",
    0x46: "12.0",
    0x47: "12.5",
    0x48: "13.0",
    0x49: "13.5",
    0x4A: "14.0",
    0x4B: "14.5",
    0x4C: "15.0",
    0x4D: "15.5",
    0x4E: "16.0",
    0x4F: "17.0",
    0x50: "18.0",
    0x51: "19.0",
    0x52: "20.0",
    0x53: "21.0",
    0x54: "22.0",
    0x55: "23.0",
    0x56: "24.0",
    0x57: "25.0",
    0x58: "26.0",
    0x59: "27.0",
    0x5A: "28.0",
    0x5B: "29.0",
    0x5C: "30.0",
    0x5D: "31.0",
    0x5E: "32.0",
    0x5F: "34.0",
    0x60: "36.0",
    0x61: "38.0",
    0x62: "40.0",
    0x63: "42.0",
    0x64: "44.0",
    0x65: "46.0",
    0x66: "48.0",
    0x67: "50.0",
    0x68: "52.0",
    0x69: "54.0",
    0x6A: "56.0",
    0x6B: "58.0",
    0x6C: "60.0",
    0x6D: "62.0",
    0x6E: "64.0",
    0x6F: "68.0",
    0x70: "72.0",
    0x71: "76.0",
    0x72: "80.0",
    0x73: "84.0",
    0x74: "88.0",
    0x75: "92.0",
    0x76: "96.0",
    0x77: "100",
    0x78: "104",
    0x79: "108",
    0x7A: "112",
    0x7B: "116",
    0x7C: "120",
    0x7D: "124",
    0x7E: "128",
    0x7F: "INF",
}

DISPLAY_TO_EXPLICIT_LENGTH_CODE = {display.upper(): code for code, display in EXPLICIT_LENGTH_CODE_TO_DISPLAY.items()}

# Keep legacy aliases stable to preserve behavior of existing hardware-validated trial YAML.
LEGACY_LENGTH_ALIAS_TO_CODE = {
    "0.125": 0x00,
    "0.25": 0x02,
    "0.5": 0x06,
    "1": 0x0E,
    "2": 0x1E,
    "4": 0x2E,
    "8": 0x3E,
    "16": 0x4E,
    "32": 0x5E,
    "64": 0x6E,
    "128": 0x7E,
    "INF": 0x7F,
}


def parse_length_code(value: int | str) -> int:
    """Parse canonical length code input from integer or hex-like string."""
    if isinstance(value, int):
        code = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("length code is empty")
        code = int(text, 16) if text.lower().startswith("0x") else int(text, 10)
    else:
        raise ValueError(f"length code must be int or string: {value}")

    if code < 0x00 or code > 0x7F:
        raise ValueError(f"length code out of range: {code} (expected 0x00..0x7F)")
    return code


def explicit_length_code_to_sixteenth_units(code: int) -> Fraction:
    """Convert explicit length code to exact length in sixteenth-note units."""
    if code < 0x00 or code > 0x7F:
        raise ValueError(f"length code out of range: {code} (expected 0x00..0x7F)")

    if code == 0x7F:
        raise ValueError("INF (0x7F) does not map to finite sixteenth units")

    if code <= 0x1E:
        return Fraction(1, 8) + Fraction(code, 16)
    if code <= 0x2E:
        return Fraction(17, 8) + Fraction(code - 0x1F, 8)
    if code <= 0x3E:
        return Fraction(17, 4) + Fraction(code - 0x2F, 4)
    if code <= 0x4E:
        return Fraction(17, 2) + Fraction(code - 0x3F, 2)
    if code <= 0x5E:
        return Fraction(17, 1) + Fraction(code - 0x4F, 1)
    if code <= 0x6E:
        return Fraction(34, 1) + Fraction((code - 0x5F) * 2, 1)
    return Fraction(68, 1) + Fraction((code - 0x6F) * 4, 1)


def find_exact_length_code_for_sixteenth_units(units: Fraction) -> int | None:
    """Find exact explicit finite code for a sixteenth-unit length, else None."""
    target = Fraction(units)
    for code in range(0x00, 0x7F):
        if explicit_length_code_to_sixteenth_units(code) == target:
            return code
    return None
