# PATTERN総STEP 解析結果

## 目的

PATTERN-wideモードにおける総STEP値の格納位置、7-bit packing、ページ境界の扱いを特定する。

## 実験系列

Triggerなし、PATTERN-wideモードで、BASE 16から以下の値を比較した。

```text
2, 3, 4, 5, 8, 15, 17, 32, 33, 64, 128
```

## 確定した結果

### 1. PATTERN-wide総STEP値

PATTERN-wide値のpayloadはphysical offset `101507` に格納される。128ではMSBがpacking control `101506` のmask `0x40` に格納される。

```text
total_steps = low7 + (128 if control & 0x40 else 0)
```

| 表示値 | `101506` | `101507` |
|---:|---:|---:|
| 2 | `0x00` | `0x02` |
| 16 | `0x00` | `0x10` |
| 17 | `0x00` | `0x11` |
| 32 | `0x00` | `0x20` |
| 33 | `0x00` | `0x21` |
| 64 | `0x00` | `0x40` |
| 128 | `0x40` | `0x00` |

### 2. PATTERN-wide変更時は16 Track分の内部値も同期される

PATTERN-wideモードで総STEPを変更すると、`101507` に加え、以下の16箇所も同値に更新される。

| Track対応 | Payload offset |
|---:|---:|
| 1 | `1347` |
| 2 | `2703` |
| 3候補 | `4060` |
| 4候補 | `5416` |
| 5候補 | `6773` |
| 6候補 | `8129` |
| 7候補 | `9486` |
| 8候補 | `10843` |
| 9候補 | `12199` |
| 10候補 | `13556` |
| 11候補 | `14912` |
| 12候補 | `16269` |
| 13候補 | `17625` |
| 14候補 | `18982` |
| 15候補 | `20339` |
| 16候補 | `21695` |

Track 1とTrack 2はper-track実験で個別対応が確認済みである。Track 3〜16の対応順は、PATTERN-wide変更で同じ値を反映することから強く推定されるが、個別編集では未確認である。

### 3. 16/17および32/33境界に固有fieldは見つからない

Triggerなし比較では、`15 → 17` および `32 → 33` の変化は総STEPpayload群とintegrity候補だけで説明できた。ページ境界専用の追加fieldは観測されていない。

### 4. 128では各同期先のpacking control更新が必要

`128 = 0x80` のため、17個のpayloadはlow7 `0x00` となり、各payloadに対応するpacking control bitを立てる必要がある。対応表は `spec.yaml` に記載する。

## Harmony Cloudでの書き込み規則

PATTERN-wideの完成状態を生成する場合、modeをwideに設定した上で、`101507` とTrack 1〜16の総STEP値を同一値へ同期して書き込む。128では各control maskも更新する。
