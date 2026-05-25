# Trigger Step state page境界（17以降）解析結果

## 目的

`total_steps: 128` 環境で、Step 17以降の page 境界を跨いでも Step state 位置式が維持されるかを確認する。

## 固定条件

- pattern_mode: PATTERN-wide
- total_steps: 128
- tempo: 120.0
- speed: 1
- trigger: 1個（比較対象stepのみ）
- velocity: track default
- length: track default
- note: C5

## 入力系列

- 基準: `BASE_EMPTY_STEPS128`（先頭と再取得の2回）
- Track 2: Step 16/17/32/33/48/49/64/65/80/81/96/97/112/113/127/128
- Track 8: Step 16/17/64/65/128

リネーム済み系列は `captures/Track_Step_State_Table_Page/` を参照。

## 主要結果

### 1. Trigger record は page境界でも既知仕様どおり

- offset 21720: 0-based track index（Track 2=0x01, Track 8=0x07）
- offset 21721: 0-based step index（16->0x0F, 17->0x10, ..., 128->0x7F）

### 2. Step state 位置式は 128step 範囲でも維持

7-bit unpack後 payload 上で、Step state entry 先頭は次式に一致した。

```text
trackIndex = trackNumber - 1
stepIndex  = stepNumber - 1

logical_entry_offset = 4 + 1187 * trackIndex + 2 * stepIndex
```

確認した page 境界:

- 16/17
- 32/33
- 48/49
- 64/65
- 80/81
- 96/97
- 112/113
- 127/128

上記すべてで offset 連続性（+2/step）が維持された。

### 3. 物理diffは境界で2〜3byteに見える

境界跨ぎでも、7-bit packing control byte の更新が混ざるため物理差分は 2〜3byte（時にそれ以上）に見える。

これは位置式の破綻ではなく、packing表現の差である。

### 4. BASE_EMPTY再取得は一致

`01_EmptySteps128` と `18_EmptySteps128Reimport` は `difference_count: 0`。

## 追加観測（値の意味は未確定）

位置式は確定した一方、decoded 2byte 値の意味は未確定。

- total_steps=128 の観測では second byte が `0x01/0x11/0x81/0x91` などに分岐
- Track2 Step127 で first byte `0x83` を観測

よって、**位置式は確定**、**値の意味は継続解析** とする。

## 実装への含意

- Step 17以降も個別offset収集は不要
- unpack後 payload に対して式で entry を特定して書き込み可能
- 物理offset例外処理は pack/unpack 層へ集約する
