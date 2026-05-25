# Trigger Track Field 解析結果

## 目的

Trigger record 内で Track を表す field を特定し、slot 配置モデルが Track 共通かどうかを確認する。

## 固定条件

- PATTERN-wide
- total steps 16
- tempo 120.0
- speed 1
- Velocity / Length は Track 既定値継承
- Trigger は常に 1 個
- Step 1 / C5 を使用

## 実験系列

```text
1. empty
2. Track 1 / Step 1 / C5
3. empty after Track 1
4. Track 2 / Step 1 / C5
5. empty after Track 2
...
16. Track 8 / Step 1 / C5
17. empty after Track 8
```

## 確定した結果

### 1. Trigger record byte 0 は Track index（0-based）

slot 1 の payload offset 21720 は、Track 1〜8 で次のように変化した。

| Track | offset 21720 |
|---:|---:|
| 1 | 0x00 |
| 2 | 0x01 |
| 3 | 0x02 |
| 4 | 0x03 |
| 5 | 0x04 |
| 6 | 0x05 |
| 7 | 0x06 |
| 8 | 0x07 |

このため、通常 Trigger record は次の形で扱える。

```text
[track_index, step_index, pitch, velocity, length, field_5]
```

### 2. Trigger slot array は Track 共通領域

Track 1〜8 のいずれでも、Trigger record は同じ slot 1 周辺へ書かれる。Track 追加時の主な共通変更は以下。

- 21714: packing control
- 21720: track index
- 21721: step index
- 21722: packing control
- 21723: pitch

## Step state 側の観測

Trigger record は Track 共通領域だが、Step state 側は Track 別ブロックが存在する。

Track 1〜8 の Step 1 では、active flag 候補として以下を観測した。

| Track | active flag 候補 offset |
|---:|---:|
| 1 | 16 |
| 2 | 1373 |
| 3 | 2729 |
| 4 | 4086 |
| 5 | 5443 |
| 6 | 6799 |
| 7 | 8156 |
| 8 | 9512 |

## 重要な注意

Trigger を削除しても、各 Track の Step state block で初期化由来の値が残る場合がある。
そのため EmptyAfterTrackN は Trigger 不在の状態ではあるが、BASE_EMPTY と byte-identical ではない。

## 実装への含意

- Trigger record 側は Track index を byte 0 に書く実装で確定できる。
- Step state 側は Track 別で、全 Track・全 Step の一般式は未確定。
- 今後の差分実験では「削除で空に戻す」よりも「毎回 BASE_EMPTY 再読込」を基準にするのが安全。
