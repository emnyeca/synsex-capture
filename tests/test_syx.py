from pathlib import Path

from digitone_syx_toolkit.syx import extract_sysex_messages, load_syx_file, save_syx_file


def test_extract_sysex_messages_multiple_packets():
    raw = bytes([0x00, 0xF0, 0x01, 0xF7, 0x12, 0xF0, 0x7D, 0x10, 0xF7])
    packets = extract_sysex_messages(raw)
    assert packets == [bytes([0xF0, 0x01, 0xF7]), bytes([0xF0, 0x7D, 0x10, 0xF7])]


def test_save_and_load_syx_roundtrip(tmp_path: Path):
    messages = [bytes([0xF0, 0x7D, 0x01, 0xF7]), bytes([0xF0, 0x7D, 0x02, 0xF7])]
    out = tmp_path / "sample.syx"
    save_syx_file(messages, out)
    loaded = load_syx_file(out)
    assert loaded == messages
