# Digitone II Pattern SysEx 解析結果 — 対象別ドキュメント

## このディレクトリの位置づけ

このディレクトリは、Harmony Cloud が Digitone II 向け Pattern SysEx を生成するために必要な範囲の解析結果を、解析対象ごとに整理したものです。

解析の正本は、実機から取得した `.syx` と、そのバイナリ比較結果です。`datasets/analysis/` に含まれる `summary.yaml`、`*_confirmed.yaml`、`*_inference.yaml` は解析補助として参照しますが、それ自体を仕様の根拠とはしません。本文および `spec.yaml` では、制御された比較実験で確認できた事項と、まだ仮説に留まる事項を区別しています。

## ステータス表記

| 表記 | 意味 |
|---|---|
| `confirmed` | 制御実験の差分で特定済み |
| `observed` | 該当実験で観測済みだが一般化は限定的 |
| `inferred` | 観測から有力だが追加確認余地あり |
| `out_of_scope` | Harmony Cloud の現在用途では追跡しない |

## 解析対象一覧

| 対象 | 結果 | 仕様 |
|---|---|---|
| Trigger record / slot allocation | [analysis](trigger-record/analysis.ja.md) | [spec](trigger-record/spec.yaml) |
| Trigger pitch | [analysis](trigger-pitch/analysis.ja.md) | [spec](trigger-pitch/spec.yaml) |
| Trigger velocity / track default | [analysis](trigger-velocity/analysis.ja.md) | [spec](trigger-velocity/spec.yaml) |
| Trigger length / track default | [analysis](trigger-length/analysis.ja.md) | [spec](trigger-length/spec.yaml) |
| Pattern tempo | [analysis](pattern-tempo/analysis.ja.md) | [spec](pattern-tempo/spec.yaml) |
| Pattern speed | [analysis](pattern-speed/analysis.ja.md) | [spec](pattern-speed/spec.yaml) |
| Pattern total steps | [analysis](pattern-total-steps/analysis.ja.md) | [spec](pattern-total-steps/spec.yaml) |
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

## Harmony Cloud に必要な確定事項の要約

| 項目 | 確定内容 |
|---|---|
| Trigger record | 7-bit unpack後に6 byte固定長slotとして扱える |
| Step index | record byte `1`、0始まり |
| Pitch | record byte `2`、半音単位整数 |
| Velocity | record byte `3`、`0xFF` はTrack既定値継承 |
| Length | record byte `4`、`0xFF` はTrack既定値継承、`0x7F` は明示 `INF` |
| Track default velocity | physical offset `1333` |
| Track default length | physical offset `1334` |
| Pattern tempo | offsets `101498`, `101503`, `101504`、`round(BPM * 120)` |
| Pattern speed | offset `101512`、列挙コード |
| Pattern total steps mode | offset `101511`、wide=`0x00`、per-track=`0x01` |
| Pattern-wide total steps | offset `101507` と各Track値の同期更新 |

## 既存実装への注意

現行の `profiles/digitone2.default.yaml` と `src/digitone_syx_toolkit/events_to_syx.py` は、今回の解析結果と整合しない部分があります。実装修正は別工程としますが、少なくとも次はそのまま採用できません。

1. Trigger slot を `(step, track)` ごとの固定offsetとして扱うモデル。Trigger recordは、Step位置ではなく空きslotへ割り当てられ、削除後も後続slotは前詰めされません。
2. `length_codes["1"] = 0x7F` という解釈。raw payload `0x7F` はpacking controlと併せて読む必要があり、継承 `0xFF` と明示 `INF` `0x7F` は別です。明示Length `1` は `0x0E` です。
3. Pattern length をoffset `1347` のみで書くモデル。PATTERN-wide設定では、mode、pattern-wide値、Track 1〜16値、128用packing controlの取り扱いが必要です。
4. Trigger pitchへ入力MIDI noteをそのまま書くモデル。今回の実験ではDigitone表示 `C5` が格納値 `0x3C` でした。イベント側の音名／MIDIオクターブ規約を明確にして変換する必要があります。

## 未完了の解析

Checksum / integrity field については、変更済みraw byteの加算差分が `114113–114114` に追随する観測が蓄積されていますが、加算対象範囲と完全再計算式はまだ最終確認前です。このディレクトリには確定仕様としては収録せず、Checksum解析完了後に追加します。
