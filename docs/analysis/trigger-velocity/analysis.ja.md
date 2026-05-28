# Trigger Velocity / Track Default Velocity 解析結果

## 目的

Trigger個別Velocityのfieldを特定し、新規TriggerがTrack既定値を継承する仕組みと、明示値の保持挙動を確認する。

## 実験系列

```text
空状態
→ Step 1 / C5 を追加（Track既定Velocity 100）
→ Step Velocity 1
→ Step Velocity 100
→ Track既定Velocity 1
→ Step Velocity 1
→ Step削除
→ Step 1 / C5 を追加（Track既定Velocity 1）
→ Step Velocity 100
→ Track既定Velocity 100
```

## 確定した結果

### Track既定Velocity

Track 1〜8の既定Velocityは、各Trackの専用physical offsetに実値で格納される。

| Track | Offset |
|---:|---:|
| 1 | `1333` |
| 2 | `2689` |
| 3 | `4046` |
| 4 | `5403` |
| 5 | `6759` |
| 6 | `8116` |
| 7 | `9472` |
| 8 | `10829` |

| Track既定Velocity | Byte値 |
|---:|---:|
| 1 | `0x01` |
| 50 | `0x32` |
| 70 | `0x46` |
| 100 | `0x64` |

### Trigger個別Velocity

Trigger slot 1のVelocity payloadはphysical offset `21724`、7-bit unpack後のrecord byte `3` である。

| 状態 | Decoded record byte 3 | 意味 |
|---|---:|---|
| 新規Trigger、Track既定値を使用 | `0xFF` | Track default継承 |
| 個別Velocity 1 | `0x01` | 明示値 |
| 個別Velocity 64 | `0x40` | 明示値 |
| 個別Velocity 100 | `0x64` | 明示値 |
| 個別Velocity 127 | `0x7F` | 明示値 |

### 継承と明示値は、実効値が同じでも別状態

Track既定Velocityが100のとき、新規Triggerは実効Velocity 100で鳴るがfieldは `0xFF` である。一度Velocityを変更して100へ戻すとfieldは `0x64` となる。Track既定Velocityが1のケースでも同様に、新規Triggerは `0xFF`、明示的に1へ変更したTriggerは `0x01` となる。

明示値を持ったTriggerは、後からTrack既定Velocityを変更しても値が書き換わらない。

## Packing上の注意

継承値 `0xFF` はraw SYX上ではpayload `0x7F` とcontrol byte側のMSBで表現される。raw payload `0x7F` だけを見て、明示Velocity 127と継承を同一視してはならない。

## Checksumに関する観測

Checksum下位byteは physical offset `114114`。Track既定Velocityのみを変更した差分でもこのbyteが追随して変化するため、Track既定Velocity書き換え後はchecksum再計算が必須。
