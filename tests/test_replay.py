from __future__ import annotations

from pathlib import Path

from digitone_syx_toolkit.replay import (
    load_sysex_messages_from_files,
    replay_sysex,
    replay_sysex_bundle,
    replay_sysex_files,
)
from digitone_syx_toolkit.syx import save_syx_file


class _DummyOutPort:
    def __init__(self, sent: list[bytes]):
        self._sent = sent

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def send(self, msg):
        self._sent.append(bytes(msg.bytes()))


def _write_syx(path: Path, packets: list[bytes]) -> Path:
    return save_syx_file(packets, path)


def test_load_sysex_messages_from_files_keeps_order(tmp_path: Path):
    f1 = _write_syx(tmp_path / "01_intro.syx", [b"\xF0\x01\xF7"])
    f2 = _write_syx(tmp_path / "02_a.syx", [b"\xF0\x02\xF7", b"\xF0\x03\xF7"])

    messages = load_sysex_messages_from_files([f1, f2])

    assert messages == [b"\xF0\x01\xF7", b"\xF0\x02\xF7", b"\xF0\x03\xF7"]


def test_replay_sysex_files_sends_packets_in_file_order(tmp_path: Path, monkeypatch):
    sent_packets: list[bytes] = []
    sleep_calls: list[float] = []

    f1 = _write_syx(tmp_path / "01_intro.syx", [b"\xF0\x11\xF7"])
    f2 = _write_syx(tmp_path / "02_a.syx", [b"\xF0\x12\xF7", b"\xF0\x13\xF7"])

    monkeypatch.setattr("digitone_syx_toolkit.replay.mido.open_output", lambda _name: _DummyOutPort(sent_packets))
    monkeypatch.setattr("digitone_syx_toolkit.replay.time.sleep", lambda sec: sleep_calls.append(sec))

    sent = replay_sysex_files(
        out_port_name="Dummy Out",
        syx_files=[f1, f2],
        delay_ms=10,
    )

    assert sent == 3
    assert sent_packets == [b"\xF0\x11\xF7", b"\xF0\x12\xF7", b"\xF0\x13\xF7"]
    assert sleep_calls == [0.01, 0.01, 0.01]


def test_replay_sysex_bundle_reads_concatenated_packets(tmp_path: Path, monkeypatch):
    sent_packets: list[bytes] = []

    bundle = _write_syx(
        tmp_path / "blue_moon.bundle.syx",
        [b"\xF0\x21\xF7", b"\xF0\x22\xF7", b"\xF0\x23\xF7"],
    )

    monkeypatch.setattr("digitone_syx_toolkit.replay.mido.open_output", lambda _name: _DummyOutPort(sent_packets))

    sent = replay_sysex_bundle(
        out_port_name="Dummy Out",
        bundle_syx_file=bundle,
        delay_ms=0,
    )

    assert sent == 3
    assert sent_packets == [b"\xF0\x21\xF7", b"\xF0\x22\xF7", b"\xF0\x23\xF7"]


def test_replay_sysex_direct_packets_unchanged(monkeypatch):
    sent_packets: list[bytes] = []
    monkeypatch.setattr("digitone_syx_toolkit.replay.mido.open_output", lambda _name: _DummyOutPort(sent_packets))

    packets = [b"\xF0\x31\xF7", b"\xF0\x32\xF7"]
    sent = replay_sysex(out_port_name="Dummy Out", messages=packets)

    assert sent == 2
    assert sent_packets == packets
