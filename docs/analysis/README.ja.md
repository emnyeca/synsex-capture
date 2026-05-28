# Digitone II Pattern SysEx 解析結果 — 対象別ドキュメント

## このディレクトリの位置づけ

このディレクトリは、EUB Changes が Digitone II 向け Pattern SysEx を生成するために必要な範囲の解析結果を、解析対象ごとに整理したものです。

解析の正本は、実機から取得した `.syx` と、そのバイナリ比較結果です。`datasets/analysis/` に含まれる `summary.yaml`、`*_confirmed.yaml`、`*_inference.yaml` は解析補助として参照しますが、それ自体を仕様の根拠とはしません。本文および `spec.yaml` では、制御された比較実験で確認できた事項と、まだ仮説に留まる事項を区別しています。

## ステータス表記

| 表記 | 意味 |
|---|---|
| `confirmed` | 制御実験の差分で特定済み |
| `observed` | 該当実験で観測済みだが一般化は限定的 |
| `inferred` | 観測から有力だが追加確認余地あり |
| `out_of_scope` | EUB Changes の現在用途では追跡しない |

## 解析対象一覧

| 対象 | 結果 | 仕様 |
|---|---|---|
| Trigger record / slot allocation | [analysis](trigger-record/analysis.ja.md) | [spec](trigger-record/spec.yaml) |
| Trigger track field | [analysis](trigger-track/analysis.ja.md) | [spec](trigger-track/spec.yaml) |
| Trigger step-state table (track-wise) | [analysis](trigger-step-state-table/analysis.ja.md) | [spec](trigger-step-state-table/spec.yaml) |
| Trigger step-state page boundary (steps 17+) | [analysis](trigger-step-state-page/analysis.ja.md) | [spec](trigger-step-state-page/spec.yaml) |
| Trigger pitch | [analysis](trigger-pitch/analysis.ja.md) | [spec](trigger-pitch/spec.yaml) |
| Trigger velocity / track default | [analysis](trigger-velocity/analysis.ja.md) | [spec](trigger-velocity/spec.yaml) |
| Trigger length / track default | [analysis](trigger-length/analysis.ja.md) | [spec](trigger-length/spec.yaml) |
| Pattern tempo | [analysis](pattern-tempo/analysis.ja.md) | [spec](pattern-tempo/spec.yaml) |
| Pattern speed | [analysis](pattern-speed/analysis.ja.md) | [spec](pattern-speed/spec.yaml) |
| Pattern total steps | [analysis](pattern-total-steps/analysis.ja.md) | [spec](pattern-total-steps/spec.yaml) |
| Pattern name | [analysis](pattern-name/analysis.ja.md) | [spec](pattern-name/spec.yaml) |
| Pattern-wide / per-track mode | [analysis](pattern-step-mode/analysis.ja.md) | [spec](pattern-step-mode/spec.yaml) |
| Total steps expansion / hide-reshow behavior | [analysis](pattern-total-steps-propagation/analysis.ja.md) | [spec](pattern-total-steps-propagation/spec.yaml) |

## 共通固定条件

以下の条件を固定した差分系列を主に使用しています。

| 項目 | 値 |
|---|---|
| PROJECT番号 | `002` |
| PROJECT名 | `NEW PROJECT` |
| PATTERN番号 | `A01` |
| PATTERN名 | `UNTITLED` |
| MIDI PORTS / OUTPUT TO | `USB` |

## EUB Changes に必要な確定事項の要約

| 項目 | 確定内容 |
|---|---|
| Trigger record | 7-bit unpack後に6 byte固定長slotとして扱える |
| Trigger track index | record byte `0`、0始まり（Track 1〜8で確認） |
| Step index | record byte `1`、0始まり |
| Pitch | record byte `2`、半音単位整数 |
| Velocity | record byte `3`、`0xFF` はTrack既定値継承 |
| Length | record byte `4`、`0xFF` はTrack既定値継承、`0x7F` は明示 `INF` |
| Track default velocity | Track 1..8 offsets `1333`, `2689`, `4046`, `5403`, `6759`, `8116`, `9472`, `10829` |
| Track default length | physical offset `1334` |
| Pattern tempo | offsets `101498`, `101503`, `101504`、`round(BPM * 120)` |
| Pattern speed | offset `101512`、列挙コード |
| Pattern total steps mode | offset `101511`、wide=`0x00`、per-track=`0x01` |
| Pattern-wide total steps | offset `101507` と各Track値の同期更新 |

補足（Length full sweep 2026-05-26）:
`0x00..0x7E` の実機表示読み取りは127件を確認し、全域対応表を確定。
不足していた `1.88` を補完後、重複なし・順序整合・既知アンカー整合を確認済み。
確定データセットは `datasets/analysis/length_field_20260526/` に集約し、
EUB Changes 側の duration->Digitone Length 変換で利用可能。

## 実装反映状況（2026-05時点）

`src/digitone_syx_toolkit/digitone2/` と `src/digitone_syx_toolkit/events_to_syx.py` への移行により、次の点は解析結果へ反映済みです。

1. `(step, track)` 固定offset前提の `profile.slots` 方式を廃止し、内蔵 `BASE_EMPTY.syx` を基準に Trigger slot array へ順次配置する方式へ移行。
2. Trigger Length の扱いを更新し、`inherit=0xFF` と明示 `INF=0x7F` を分離。明示 `1` は `0x0E` として扱う実装へ変更。
3. Pattern total steps は pattern-wide 値 (`101507`) と Track 1〜16 mirror値を同期更新し、7-bit packing control を保持しながら書き換える方式へ変更。
4. Pitch 変換は Digitone表示基準（解析で確認した `C5 -> 0x3C`）を前提にした変換へ更新。

一方で、以下は未反映または部分反映です。

1. Track default velocity / length の書き換えは初期実装スコープ外として停止し、内蔵 `BASE_EMPTY.syx` の既定値維持を前提にする。
2. Step state table は 7-bit unpack 後の 2byte/step 連続テーブルとして整理し、`4 + 1187 * trackIndex + 2 * stepIndex` を実装へ反映。通常Trigger値は確認範囲で `odd=[0x03,0x81]`, `even=[0x03,0x91]` に一致し、page境界による追加分岐は未観測。
3. Trigger record byte 0 は 0-based Track index として確定（Track 1〜8）。
4. Step state 差分は packing control byte を含むため物理上 2〜3byte に見えることがあるが、意味上は decoded 2byte entry を更新するモデルへ統一。

## 未完了の解析

Checksum / integrity field については、変更済みraw byteの加算差分が `114113–114114` に追随する観測が蓄積されています。Track default velocity変更時も `114114` (checksum low byte) が追随することを確認済みです。現実装では `sum(data[10:114113]) % 16384` を用いて再計算していますが、加算対象範囲と完全再計算式の最終確定は継続課題です。Checksum解析完了後に確定仕様として追記します。

