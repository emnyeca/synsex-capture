# digitone-syx-toolkit

Digitone II などのハードウェアシンセサイザー向けに、USB/MIDI 経由の SysEx を扱う CLI デバッグツールです。

主な機能:

- MIDI 入出力ポート列挙
- SysEx キャプチャと `.syx` 保存
- `.syx` の再送信
- `.syx` 同士のバイナリ差分表示
- `.syx` の Hex Viewer
- 解析向け簡易 GUI（MIDI Capture/Replay / Diff / Hex / Selective Patch）
- キャプチャ時の YAML メタ情報出力（`datasets/`）

## Requirements

- Python 3.10+
- mido
- python-rtmidi
- PyYAML

## Install

```bash
pip install -e .
```

開発用:

```bash
pip install -e .[dev]
```

## CLI Usage

ポート番号は 1-based index（1, 2, 3...）です。ポート名も指定可能です。

```bash
digitone_syx_toolkit list_ports
```

```bash
digitone_syx_toolkit capture --in-port 1 --out-dir captures --label A01 --max-messages 10
```

```bash
digitone_syx_toolkit replay --out-port 2 --file captures/A01.syx
```

```bash
digitone_syx_toolkit diff --file1 captures/A01.syx --file2 captures/A02.syx
```

```bash
digitone_syx_toolkit view --file captures/A01.syx
```

```bash
digitone_syx_toolkit gui
```

Windows (PowerShell) では `bash digitone_syx_toolkit gui` ではなく、次のように実行してください。

```powershell
digitone_syx_toolkit gui
```

もしコマンドが見つからない場合:

```powershell
python -m digitone_syx_toolkit gui
```

GUIの解析手順は以下を参照:

- `docs/digitone-pattern-analysis.ja.md`

### GUIで受信・再送する

1. `digitone_syx_toolkit gui` を起動
2. `MIDI Capture/Replay` タブで `Refresh Ports`
3. Input port に Digitone II を選択
4. `Start Capture` を押してから Digitone II で SysEx Send
5. 受信後 `.syx` と `datasets/*.yaml` が保存される
6. 再送する場合は同タブで Output port と `.syx` を指定して `Send to Output Port`

### Capture Metadata (YAML)

`capture` 実行時に `datasets/{label}.yaml` を出力します。例:

```yaml
file: captures/A01.syx
label: A01
captured_at: 2026-05-23T10:00:00+00:00
message_count: 4
total_bytes: 732
track: 1
step: 09
note: C4
len_display: 1/8
velocity: 96
remarks: digitone pattern test
```

追加メタ情報オプション:

- `--track`
- `--step`
- `--note`
- `--len-display`
- `--velocity`
- `--remarks`

## Error Handling / Logging

- MIDI ポート未検出、インデックス範囲外、ファイル読み込み失敗などは終了コード 1 で扱います。
- ログは標準出力に表示します。
- `--log-file path/to/log.txt` を指定するとログファイルにも出力します。
- `--verbose` で詳細ログを有効化します。

## Project Structure

```text
src/digitone_syx_toolkit/
  cli.py             # CLI command routing
  gui.py             # Tkinter analysis assistant
  midi.py            # MIDI port listing and selection helpers
  capture.py         # SysEx capture loop
  replay.py          # SysEx replay logic
  syx.py             # .syx read/write and packet parsing
  diffing.py         # byte-level diff rendering
  hexview.py         # hex dump formatting
  metadata.py        # YAML metadata output
  patcher.py         # selective byte patching from YAML
  errors.py          # domain exceptions
  logging_utils.py   # logging setup
tests/
  test_syx.py
  test_diff_hex.py
```

## Notes

- 将来 GUI (Tkinter など) へ移行しやすいよう、CLI とロジックを分離しています。
- MVP 優先で `list_ports`/`capture`/`replay` を先に成立させ、`diff`/`view`/YAML 出力を続けて実装しています。
