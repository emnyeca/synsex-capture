"""Digitone II pattern-name encoding helpers."""

from __future__ import annotations

PATTERN_NAME_MAX_CHARS = 16
PATTERN_NAME_PRIMARY_DECODED_OFFSET = 88788
PATTERN_NAME_SHADOW_DECODED_OFFSET = 89096

ALLOWED_PATTERN_NAME_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "\u00c5\u00c4\u00d6\u00dc\u00df\u00c6\u00d8\u00c7\u00d1"
    "0123456789~!@#$%^&()_+-= "
)


def normalize_pattern_name(name: str) -> str:
    """Normalize name with ASCII-only uppercasing while preserving non-ASCII chars."""
    if not isinstance(name, str):
        raise ValueError("Pattern name must be a string")

    out: list[str] = []
    for ch in name:
        code = ord(ch)
        if 0x61 <= code <= 0x7A:
            out.append(chr(code - 0x20))
        else:
            out.append(ch)
    return "".join(out)


def validate_pattern_name(name: str) -> None:
    """Validate normalized pattern name against confirmed hardware constraints."""
    if len(name) > PATTERN_NAME_MAX_CHARS:
        raise ValueError(
            f"Pattern name exceeds {PATTERN_NAME_MAX_CHARS} characters after normalization: {name!r}"
        )

    for ch in name:
        if ch not in ALLOWED_PATTERN_NAME_CHARS:
            raise ValueError(f"Unsupported pattern name character: {ch!r} in {name!r}")


def encode_pattern_name_decoded_bytes(name: str) -> bytes:
    """Encode to exactly 16 decoded bytes using confirmed null-padding behavior."""
    normalized = normalize_pattern_name(name)
    validate_pattern_name(normalized)
    encoded = normalized.encode("latin-1")
    if len(encoded) < PATTERN_NAME_MAX_CHARS:
        encoded += b"\x00" * (PATTERN_NAME_MAX_CHARS - len(encoded))
    return encoded


def write_pattern_name(decoded_payload: bytearray, name: str) -> None:
    """Write mirrored pattern-name bytes into primary and shadow decoded regions."""
    encoded = encode_pattern_name_decoded_bytes(name)

    p0 = PATTERN_NAME_PRIMARY_DECODED_OFFSET
    p1 = p0 + PATTERN_NAME_MAX_CHARS
    s0 = PATTERN_NAME_SHADOW_DECODED_OFFSET
    s1 = s0 + PATTERN_NAME_MAX_CHARS

    if p1 > len(decoded_payload) or s1 > len(decoded_payload):
        raise ValueError("Decoded payload is too short for pattern-name offsets")

    decoded_payload[p0:p1] = encoded
    decoded_payload[s0:s1] = encoded
