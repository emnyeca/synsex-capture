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
- events YAML のバリデーション
- `events.yaml + profile.yaml + template.syx` からの `.syx` 生成（実験機能）

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

```bash
digitone_syx_toolkit validate_events --file ../harmony-cloud/examples/blue_moon.events.yaml
```

```bash
digitone_syx_toolkit check_profile \
  --events ../harmony-cloud/examples/blue_moon.events.yaml
```

```bash
digitone_syx_toolkit export_missing_slots \
  --events ../harmony-cloud/examples/blue_moon.events.yaml
```

```bash
digitone_syx_toolkit build_from_events \
  --events ../harmony-cloud/examples/blue_moon.events.yaml \
  --template captures/template_empty.syx \
  --output captures/generated_from_events.syx
```

任意で `--profile` を指定すると、別機種や別マッピングを使えます。未指定時は
`profiles/digitone2.default.yaml` を使用します。

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

### GUIで events.yaml から .syx を生成する

1. `digitone_syx_toolkit gui` を起動
2. `Events -> SYX` タブを開く
3. `Events YAML`, `Profile YAML`, `Template .syx`, `Output .syx` を設定
4. `Validate Events YAML` で事前チェック
5. `Check Profile Coverage` で不足する `(step, track)` を確認
6. 不足がある場合は `Export Missing Slots` で不足テンプレート YAML を出力
7. 出力したテンプレートの各 `offset_*` を埋める
8. 埋めたスロットを `profiles/digitone2.default.yaml` の `slots` に追加
9. もう一度 `Check Profile Coverage` を実行して `missing=0` を確認
10. `Generate SYX from Events` を実行

注意:

- 既定プロファイル (`profiles/digitone2.default.yaml`) は Digitone II 向けです。
- ただし現状は部分定義のため、未定義の `(step, track)` がある場合は `check_profile` で不足一覧が表示されます。
- Digitone II のチェックサムは生成時に自動再計算されます。

### events.yaml から「実機送信できる .syx」を作るための条件

以下が満たされると、`events.yaml -> .syx` の成功率が上がります。

1. `check_profile` が `missing=0` を返すこと
2. `profiles/digitone2.default.yaml` の `length_codes` が利用する duration をカバーしていること
3. テンプレートが Digitone II 形式であること（チェックサム領域を含むこと）

現実的な運用:

1. `Generate SYX from Events` で生成
2. 実機送信を試す
3. 拒否されたら、主に `profile.slots` と `length_codes` の未解決マッピングを疑って差分比較する

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
  events_yaml.py     # events assignment YAML validation
  events_to_syx.py   # events/profile/template based syx builder
  errors.py          # domain exceptions
  logging_utils.py   # logging setup
tests/
  test_syx.py
  test_diff_hex.py
  test_events_yaml.py
  test_events_to_syx.py
```

## Notes

- 将来 GUI (Tkinter など) へ移行しやすいよう、CLI とロジックを分離しています。
- MVP 優先で `list_ports`/`capture`/`replay` を先に成立させ、`diff`/`view`/YAML 出力を続けて実装しています。
