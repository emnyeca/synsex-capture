# Trigger Track別 Step state table 解析結果

## 目的

Track別 Step state table を、物理SYX差分ではなく 7-bit unpack 後の論理payloadで規則化する。

## 実験系列

1. BASE_EMPTY
2. Track 2 / Step 1 / C5
3. BASE_EMPTY 再インポート
4. Track 2 / Step 2 / C5
5. BASE_EMPTY 再インポート
6. Track 2 / Step 3 / C5
7. BASE_EMPTY 再インポート
8. Track 2 / Step 16 / C5
9. BASE_EMPTY 再インポート
10. Track 8 / Step 1 / C5
11. BASE_EMPTY 再インポート
12. Track 8 / Step 2 / C5
13. BASE_EMPTY 再インポート
14. Track 8 / Step 16 / C5

取得レンジ `capture_20260525_115407_0019..0034` では、誤取得を次のとおり除外した。

- `0030`: `0028` と byte-identical（Track8 / Step1 の重複）
- `0031`: 余分な BASE_EMPTY

正規系列は `captures/Track_Step_State_Table/` に 14件として再配置した。

## 結論

Step state table は規則化できる。

- 物理SYX差分の 2〜3byte は意味上の record ではない。
- Step state の実体は unpack 後 payload 上の 2byte/step 連続テーブル。
- 3箇所変化に見えるのは、論理2byteに加えて packing control byte が更新されるため。

## 1. Trigger record 側（確定事項）

slot 1 の既知仕様は本系列でも維持された。

| 内容 | Offset | Track 2 | Track 8 |
|---|---:|---:|---:|
| Track index | 21720 | 0x01 | 0x07 |
| Step index | 21721 | 0x00 / 0x01 / 0x02 / 0x0F | 0x00 / 0x01 / 0x0F |
| Pitch C5 | 21723 | 0x3C | 0x3C |
| Record byte 5 | 21726 | 0x00 | 0x00 |

Trigger record は次で扱える。

```text
Trigger record = 6 decoded bytes

byte 0: Track index, 0-based
byte 1: Step index, 0-based
byte 2: Pitch code
byte 3: Velocity field
byte 4: Length field
byte 5: 通常Triggerでは 0x00（意味は未確定）
```

## 2. Step state の物理差分は triplet record ではない

例: Track 2 / Step 1

```yaml
1370: 0x00 -> 0x10
1372: 0x00 -> 0x03
1373: 0x00 -> 0x01
```

`1370` は state本体ではなく packing control byte。unpack 後の論理値は次。

```text
Track 2 / Step 1 step-state = [0x03, 0x81]
```

Track 2 / Step 2 では、

```yaml
1370: 0x00 -> 0x04
1374: 0x00 -> 0x03
1375: 0x10 -> 0x11
```

unpack 後は、

```text
Track 2 / Step 2 step-state = [0x03, 0x91]
```

Track 8 でも同じモデルで説明できる。

## 3. Unpack後は 2byte/step の連続テーブル

Track 2 の論理entry先頭index:

| Step | 論理entry先頭index | Step 1 からの差 |
|---:|---:|---:|
| 1 | 1191 | 0 |
| 2 | 1193 | +2 |
| 3 | 1195 | +4 |
| 16 | 1221 | +30 |

Track 8 の論理entry先頭index:

| Step | 論理entry先頭index | Step 1 からの差 |
|---:|---:|---:|
| 1 | 8313 | 0 |
| 2 | 8315 | +2 |
| 16 | 8343 | +30 |

両者は次式に一致する。

```text
trackIndex = trackNumber - 1
stepIndex  = stepNumber - 1

logical_entry_offset =
  4
  + 1187 * trackIndex
  + 2 * stepIndex
```

## 4. Track block 間隔

Track 2 / Step 1 = 1191、Track 8 / Step 1 = 8313 なので、

```text
8313 - 1191 = 7122
7122 / (8 - 2) = 1187
```

Track間隔は論理payload上で 1187 byte。Track 1 base は `4` となり、既知の Track 1 / Step 1 観測とも整合する。

## 5. 通常Trigger ON時の Step state 値（観測範囲）

| Step | Unpack後の2byte |
|---:|---|
| 1 | [0x03, 0x81] |
| 2 | [0x03, 0x91] |
| 3 | [0x03, 0x81] |
| 16 | [0x03, 0x91] |

Track 2 / Track 8 で一致した。観測範囲では次規則に合う。

```text
odd step  -> [0x03, 0x81]
even step -> [0x03, 0x91]
```

## 6. BASE_EMPTY 再インポート挙動

`vs_step1_to_03/05/07/09/11/13` は `difference_count: 0`。本系列では empty snapshot が byte-identical に戻ることを確認した。

## 7. Harmony Cloud 実装への含意

Track 1〜8 / Step 1〜16 / 通常Trigger / 1step1trigger の範囲では、Step state 物理offsetの個別収集は不要。

1. packed領域を unpack
2. 論理offset式で entry 算出
3. 通常Triggerの2byteを書込
4. repack
5. Trigger record slot array を書込
6. checksum を更新

## 未確定（将来拡張用）

- Track 9以降（使用対象拡張時に block式確認）
- 同一Track/同一Stepの複数音（Chord構造）
- Trig Condition / Probability
- Micro Timing
- Track別 default Velocity / Length（Track 2〜8）
