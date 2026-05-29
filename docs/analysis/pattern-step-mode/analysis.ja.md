# PATTERN-wide / per-track 総STEPモード解析結果

## 目的

PATTERN総STEPが全体設定かTrack個別設定かを表すfield、およびper-track編集時のTrack値保持挙動を特定する。

## 実験系列

```text
PATTERN-wide / 総STEP16
→ per-trackへ切替（全Track表示16）
→ Track 1だけ8
→ Track 2だけ4
→ PATTERN-wideへ復帰（PATTERN総STEP16）
```

## 確定した結果

### モードfield

| モード | Physical offset `101511` |
|---|---:|
| PATTERN-wide | `0x00` |
| per-track | `0x01` |

### Track個別総STEP

per-trackモードで個別変更した結果、以下を直接確認した。

| Track | Payload offset | 変更 |
|---:|---:|---|
| 1 | `1347` | `0x10 → 0x08` |
| 2 | `2703` | `0x10 → 0x04` |

### モード復帰は個別値を同期しない

Track 1を8、Track 2を4へ変更した後にPATTERN-wideへ戻しても、`1347 = 0x08` と `2703 = 0x04` は残存した。変化したのはmode fieldのみである。

したがって、PATTERN-wideへの切替は「どのLength設定を有効として扱うか」の切替であり、各Trackの隠れた内部値をPATTERN値へ同期する操作ではない。

## EUB Changesでの扱い

EUB Changes の現在方針は per-track 生成である。したがって、出力時の扱いは次に更新する。

1. `101511 = 0x01` を設定し、per-track mode で書き込む。
2. LENGTH は Track 1〜16 の `low7_offset` と `msb_pack_offset + msb_mask` を用いて個別に書き込む。
3. SPEED は Track 1〜16 の個別 offset に書き込む。
4. CHANGE は pattern-shared control として `OFF` を出力する。
5. RESET は pattern-shared control として `INF` を出力する。

特に `101507` は mode 依存で意味が変わる。PATTERN-wide では total steps low byte だが、per-track では RESET low field になる。そのため per-track 出力では、従来の PATTERN-wide total steps writer が `101507` を触らないよう分岐が必要である。

Track 1〜16 の LENGTH / SPEED 配置、および pattern-shared CHANGE / RESET の確定表は `datasets/analysis/per_track_field_mapping_t01_t16_20260529/per_track_length_speed_pattern_controls_confirmed.yaml` を参照する。

## 実装状況（2026-05-29）

`digitone-syx-toolkit` は現在、Pattern-wide 互換入力を維持したまま per-track 出力を実装済みである。

1. Pattern-wide mode は後方互換のため継続対応する。
2. Per Track Mode では Track 1〜16 に個別 LENGTH / SPEED を書き込む。
3. CHANGE は pattern-shared `OFF`、RESET は pattern-shared `INF` を固定出力する。
4. `101507` は per-track mode で RESET low field として扱い、pattern-wide total steps payload としては書き込まない。

