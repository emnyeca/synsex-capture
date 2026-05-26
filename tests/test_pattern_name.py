from __future__ import annotations

import pytest

from digitone_syx_toolkit.digitone2.constants import CHECKSUM_SUM_END, CHECKSUM_SUM_START
from digitone_syx_toolkit.digitone2.packing import repack_7bit_region, unpack_7bit_region
from digitone_syx_toolkit.digitone2.pattern_name import (
    PATTERN_NAME_MAX_CHARS,
    PATTERN_NAME_PRIMARY_DECODED_OFFSET,
    PATTERN_NAME_SHADOW_DECODED_OFFSET,
    encode_pattern_name_decoded_bytes,
    normalize_pattern_name,
    validate_pattern_name,
    write_pattern_name,
)
from digitone_syx_toolkit.digitone2.template import load_base_empty_template


def test_normalize_ascii_lowercase_only():
    assert normalize_pattern_name("intro") == "INTRO"
    assert normalize_pattern_name("Blue Moon A") == "BLUE MOON A"
    assert normalize_pattern_name("\u00c5NGSTR\u00d6M") == "\u00c5NGSTR\u00d6M"
    assert normalize_pattern_name("\u00df") == "\u00df"


@pytest.mark.parametrize(
    "name",
    [
        "INTRO",
        "BLUE MOON A",
        "               A",
        "A               ",
        "THEME_A-01",
        "SOLO+ENDING",
        "\u00c5\u00c4\u00d6\u00dc\u00df\u00c6\u00d8\u00c7\u00d1",
        "ABCDEFGHIJKLMNOP",
    ],
)
def test_validate_accepts_supported_names(name: str):
    validate_pattern_name(name)


def test_validate_rejects_too_long_name():
    with pytest.raises(ValueError, match="exceeds 16"):
        validate_pattern_name("ABCDEFGHIJKLMNOPQ")


@pytest.mark.parametrize("name", ["THEME/A", "THEME.A"])
def test_validate_rejects_unsupported_characters(name: str):
    with pytest.raises(ValueError, match="Unsupported pattern name character"):
        validate_pattern_name(name)


def test_encode_uses_confirmed_null_padding():
    encoded = encode_pattern_name_decoded_bytes("INTRO")
    assert len(encoded) == PATTERN_NAME_MAX_CHARS
    assert encoded[:5] == b"INTRO"
    assert encoded[5:] == b"\x00" * 11


def test_encode_extended_character_sequence():
    encoded = encode_pattern_name_decoded_bytes("\u00c5\u00c4\u00d6\u00dc\u00df\u00c6\u00d8\u00c7\u00d1")
    assert encoded[:9] == bytes([0xC5, 0xC4, 0xD6, 0xDC, 0xDF, 0xC6, 0xD8, 0xC7, 0xD1])
    assert encoded[9:] == b"\x00" * 7


def test_encode_preserves_explicit_spaces_and_null_padding():
    trailing = encode_pattern_name_decoded_bytes("A               ")
    assert trailing == b"A" + (b" " * 15)

    leading = encode_pattern_name_decoded_bytes("               A")
    assert leading == (b" " * 15) + b"A"


@pytest.mark.parametrize("name", ["\u00c5AAAAAAAAAAAAAAA", "\u00c5\u00c4\u00d6\u00dc\u00df\u00c6\u00d8\u00c7\u00d1"])
def test_packing_round_trip_preserves_extended_pattern_name_bytes(name: str):
    data = bytearray(load_base_empty_template())
    decoded = unpack_7bit_region(data, start=CHECKSUM_SUM_START, end_exclusive=CHECKSUM_SUM_END)
    write_pattern_name(decoded, name)

    repack_7bit_region(
        data,
        start=CHECKSUM_SUM_START,
        end_exclusive=CHECKSUM_SUM_END,
        decoded_payload=decoded,
    )

    roundtrip = unpack_7bit_region(data, start=CHECKSUM_SUM_START, end_exclusive=CHECKSUM_SUM_END)
    expected = encode_pattern_name_decoded_bytes(name)

    p0 = PATTERN_NAME_PRIMARY_DECODED_OFFSET
    s0 = PATTERN_NAME_SHADOW_DECODED_OFFSET
    assert bytes(roundtrip[p0 : p0 + PATTERN_NAME_MAX_CHARS]) == expected
    assert bytes(roundtrip[s0 : s0 + PATTERN_NAME_MAX_CHARS]) == expected

    # For any extended byte (>=0x80), corresponding packed control bit must be set.
    for base in (PATTERN_NAME_PRIMARY_DECODED_OFFSET, PATTERN_NAME_SHADOW_DECODED_OFFSET):
        for rel, value in enumerate(expected):
            if value < 0x80:
                continue
            abs_idx = base + rel
            group = abs_idx // 7
            pos = abs_idx % 7
            control_offset = CHECKSUM_SUM_START + (group * 8)
            mask = 0x40 >> pos
            assert data[control_offset] & mask


def test_write_pattern_name_updates_primary_and_shadow():
    decoded = bytearray(114103)
    write_pattern_name(decoded, "BLUE MOON A")

    expected = encode_pattern_name_decoded_bytes("BLUE MOON A")
    p0 = PATTERN_NAME_PRIMARY_DECODED_OFFSET
    p1 = p0 + PATTERN_NAME_MAX_CHARS
    s0 = PATTERN_NAME_SHADOW_DECODED_OFFSET
    s1 = s0 + PATTERN_NAME_MAX_CHARS

    assert decoded[p0:p1] == expected
    assert decoded[s0:s1] == expected
