# Trigger Length / Track Default Length 解析結果

## 目的

Trigger個別Length、Track既定Length、および継承値と明示 `INF` の区別を特定する。

## 実験系列

```text
空状態
→ Step 1 / C5 を追加（Track既定Length 1）
→ Length 0.125 → 0.25 → 0.5 → 1 → 2
→ Track既定Length 2
→ Step削除
→ Step 1 / C5 を追加（Track既定Length 2）
→ Track既定Length 4（Stepも追従）
→ Length 8 → 16 → 32 → 64 → 128 → INF
```

## 確定した結果

### Track既定Length

Track 1の既定Lengthはphysical offset `1334` に格納される。

| 表示Length | `1334` |
|---:|---:|
| 1 | `0x0E` |
| 2 | `0x1E` |
| 4 | `0x2E` |

### Trigger個別Length

Trigger slot 1のLength payloadはphysical offset `21725`、7-bit unpack後のrecord byte `4` である。

| 表示Length | Decoded code |
|---:|---:|
| `0.125` | `0x00` |
| `0.25` | `0x02` |
| `0.5` | `0x06` |
| `1` | `0x0E` |
| `2` | `0x1E` |
| `4` | `0x2E` |
| `8` | `0x3E` |
| `16` | `0x4E` |
| `32` | `0x5E` |
| `64` | `0x6E` |
| `128` | `0x7E` |
| `INF` | `0x7F` |
| Track既定値を継承 | `0xFF` |

## 追加観測（2026-05-26）: Length code 全域 sweep

`0x00..0x7E` の全127コードを対象に、実機表示値の読み取り結果を収集した。

- 観測リスト件数: `127`
- 期待件数: `127`
- 重複: なし
- 単調増加: 維持

確定データは次に保存した。

- `datasets/analysis/length_field_20260526/length_display_sweep_confirmed_20260526.yaml`

初回転記時に1値欠落していた観測ログは次に保持する。

- `datasets/analysis/length_field_20260526/length_display_sweep_observed_20260526.yaml`

不足していた `1.88` を `1.81` と `1.94` の間に補完した結果、
`0x00..0x7E` の全127コードに対する表示値対応が連続かつ一意に確定した。

これにより、過去の sparse map（`0.125/0.25/0.5/1/2/.../128` の点観測）は
全コード表へ置き換えられた。encoder実装では decoded 値として
`inherit=0xFF` と明示 `INF=0x7F` を必ず区別する。

### 継承と明示値は別状態

Track既定Lengthが1の状態で新規追加したTriggerは `0xFF` を保持し、実効値1を継承する。一度個別Lengthを操作して1へ戻すと `0x0E` が保存される。Track既定Lengthを2へ変更しても、明示Length 2のfield `0x1E` は継承値へ正規化されない。

### 明示INFと継承をraw payloadだけで識別してはならない

raw payload `21725 = 0x7F` は、継承と明示INFの双方で現れる。7-bit packing controlを含めてunpackすると、継承は `0xFF`、明示INFは `0x7F` と区別できる。

### 削除後の未使用slotに属性payloadが残る場合がある

明示Length 2のTriggerを削除した実験では、slotを未使用化する主要fieldは解除されたが、Length payload `0x1E` が残った。slotを再利用して新規Triggerを追加すると、Lengthは継承値へ初期化された。

したがって、未使用slotを判定する際にLength payloadだけを使用してはならない。
