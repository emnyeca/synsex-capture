# PATTERN Tempo 解析結果

## 目的

PATTERN Tempoの保存field、エンコード式、Triggerとの独立性を特定する。

## 実験系列

Triggerなしの比較で、`120.0`, `120.1`, `121.0`, `130.0`, `60.0`, `300.0`, `30.0` BPMを取得した。加えて、Step 1 / C5 Triggerありの状態で `120.0 → 130.0 → 120.0` を比較した。

## 確定した結果

Tempoは16bitのscaled値を7-bit SysEx packingして格納する。

```text
scaled_tempo = round(BPM * 120)
BPM = unpacked_16bit_value / 120
```

| Physical offset | 内容 |
|---:|---|
| `101498` | 周辺payloadのMSBを保持するpacking control byte |
| `101503` | Tempo上位byteのlow 7bit |
| `101504` | Tempo下位byteのlow 7bit |

Tempoに対応するcontrol bitは、今回の配置では以下である。

| 対象 | `101498` mask |
|---|---:|
| `101503` のMSB | `0x04` |
| `101504` のMSB | `0x02` |

## 観測値

| BPM | Scaled | Unpacked hex | Packed control / hi / lo |
|---:|---:|---:|---|
| 30.0 | 3600 | `0x0E10` | `00 / 0E / 10` |
| 60.0 | 7200 | `0x1C20` | `00 / 1C / 20` |
| 120.0 | 14400 | `0x3840` | `00 / 38 / 40` |
| 120.1 | 14412 | `0x384C` | `00 / 38 / 4C` |
| 120.2 | 14424 | `0x3858` | `00 / 38 / 58` |
| 120.3 | 14436 | `0x3864` | `00 / 38 / 64` |
| 120.4 | 14448 | `0x3870` | `00 / 38 / 70` |
| 121.0 | 14520 | `0x38B8` | `02 / 38 / 38` |
| 130.0 | 15600 | `0x3CF0` | `02 / 3C / 70` |
| 300.0 | 36000 | `0x8CA0` | `06 / 0C / 20` |

## Triggerへの波及

Step 1 / C5 Triggerが存在する状態で `120.0 → 130.0 → 120.0` を行った比較では、Tempo fieldとintegrity候補のみが変化し、既知のTrigger state / record領域は不変だった。Tempo変更は通常Trigger recordを書き換えない。

## 実装上の注意

`101498` はTempo専用byteではなくpacking controlであるため、Tempoに対応するmask `0x06` のみを更新し、他bitを保持する必要がある。
