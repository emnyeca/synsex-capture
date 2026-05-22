from synsex_capture.diffing import diff_bytes
from synsex_capture.hexview import hex_dump


def test_diff_bytes_reports_offsets_and_values():
    result = diff_bytes(bytes([0xF0, 0x10, 0xF7]), bytes([0xF0, 0x11, 0xF7, 0x00]))
    assert result.len1 == 3
    assert result.len2 == 4
    assert len(result.differences) == 2
    assert result.differences[0].offset == 1
    assert result.differences[0].before == 0x10
    assert result.differences[0].after == 0x11
    assert result.differences[1].offset == 3
    assert result.differences[1].before is None
    assert result.differences[1].after == 0x00


def test_hex_dump_contains_offset_hex_and_ascii():
    text = hex_dump(b"ABC\x00XYZ")
    assert "00000000" in text
    assert "41 42 43" in text
    assert "|ABC.XYZ|" in text
