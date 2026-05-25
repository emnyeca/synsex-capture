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

## Harmony Cloudでの扱い

Harmony CloudはPATTERN-wideのみを生成対象とするため、出力時には次を行うべきである。

1. `101511 = 0x00` を設定する。
2. PATTERN-wide総STEP値を設定する。
3. Track 1〜16の総STEP値を同じ値へ同期し、既存編集履歴に由来する非表示値を正規化する。

この正規化は実機の「modeだけを戻す」操作と同じではないが、完成Patternを一括生成する用途では整合した出力になる。
