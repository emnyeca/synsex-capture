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
- Digitone II 向け `.syx` 生成（内蔵空 PATTERN テンプレート方式）

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
digitone_syx_toolkit build_from_events \
  --events ../harmony-cloud/examples/blue_moon.events.yaml
```

`--output` を省略した場合は、`captures/generated/<eventsファイル名>.syx` に保存されます。
`*.events.yaml` / `*.events.yml` の場合は `.events` と拡張子を除いた名前になります。

補足: `--template` は解析/デバッグ用の上書き入力です。通常の生成では不要です。

```bash
digitone_syx_toolkit gui
```

Windows (PowerShell) では `bash digitone_syx_toolkit gui` ではなく、次のように実行してください。

```powershell
digitone_syx_toolkit gui
```

もしコマンドが見つからない場合:

```powershell
python -m pip install -e .
digitone_syx_toolkit gui
```

GUIの解析手順は以下を参照:

- `docs/digitone-pattern-analysis.ja.md`

### GUIで受信・再送する

1. `digitone_syx_toolkit gui` を起動
2. `MIDI Capture/Replay` タブで `Refresh Ports`
3. Input port に Digitone II を選択
4. `Start Capture` を押してから Digitone II で SysEx Send
5. 受信ごとに `.syx` と `datasets/*.yaml` が連続保存される（`label_0001.syx` 形式）
6. 再送する場合は同タブで Output port と `.syx` を指定して `Send to Output Port`

補足:

- GUI の `Max messages` が空欄なら自動停止しません
- 停止は `Stop Capture`、または `Max messages` / `Duration sec` 到達時です

### GUIで events.yaml から Digitone II 用 .syx を生成する

本機能は Digitone II 向けの内蔵空 PATTERN テンプレートを基準に、
`events.yaml` から完成状態の `.syx` を生成する方針です。

1. `digitone_syx_toolkit gui` を起動
2. `Events -> SYX` タブを開く
3. `Events YAML` を設定（`Output .syx` はデフォルトで自動入力）
4. `Validate Events YAML` で形式と制約を確認
5. `Generate Digitone II SYX` を実行
6. 必要に応じて生成した `.syx` を `MIDI Capture/Replay` タブから送信

生成時に自動で行う処理:

- 内蔵空 PATTERN テンプレートの読み込み
- PATTERN-wide mode の設定
- Tempo / SPEED / total steps の設定
- Trigger slot array への record 配置
- Step state table の更新
- Velocity / Length の inherit 値処理
- 7-bit packing control の更新
- Checksum の更新（未確定事項は下記参照）

注意:

- 現状は Digitone II 専用です。
- 空 PATTERN からの新規生成を前提とします。
- PATTERN-wide のみ対応です。
- Track 1〜8、Step 1〜128 の通常 Trigger のみ対応です。
- 同一 Track / 同一 Step への複数 Trigger（Chord）は未対応です。
- Track default（tracks セクション）書き換えは未対応です。
- 既存 PATTERN の非破壊編集は未対応です。

### events.yaml から「実機送信できる .syx」を作るための条件

以下が満たされると、`events.yaml -> .syx` の成功率が上がります。

1. `events.yaml` に pattern 設定（mode/tempo/speed/total_steps）が含まれていること
2. event ごとの velocity/length で `inherit` と明示値を区別していること
3. 生成結果が実機受理される checksum 条件を満たしていること

現実的な運用:

1. `Generate SYX from Events` で生成
2. 実機送信を試す
3. 拒否されたら、checksum と 7-bit packing 更新結果を差分比較する

推奨 `events.yaml` 例:

```yaml
version: 1
device: digitone2

pattern:
  mode: pattern-wide
  tempo: 120.0
  speed: "1/8"
  total_steps: 128

events:
  - step: 1
    track: 1
    note: C5
    velocity: inherit
    length: inherit

  - step: 17
    track: 2
    note: D5
    velocity: 84
    length: "2"

  - step: 128
    track: 8
    note: G4
    velocity: inherit
    length: "INF"
```

補足:

- `velocity: inherit` と `velocity: 100` は内部表現が異なります。
- `length: inherit` と `length: "1"` も内部表現が異なります。
- `tracks:` セクションは初期対応範囲外のため validation error になります。

### 生成済み実機試験ファイル

実機試験向けの最小生成サンプルは次に保存します。

- `captures/generated/trial1_minimal_trigger.syx`
- `captures/generated/trial2_page_track_cross.syx`

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
  events_to_syx.py   # Digitone II 向け syx builder（内蔵テンプレート方式へ移行中）
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
