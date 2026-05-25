# Trigger Pitch 解析結果

## 目的

Step位置を固定し、音高だけを変更することで、Trigger record内のPitch fieldと保存値体系を特定する。

## 実験系列

```text
空状態
→ Step 1 / C5
→ Step 1 / C#5
→ Step 1 / D5
→ Step 1 / C4
```

## 結果

音高変更では、Trigger本体として変化したpayloadはphysical offset `21723` のみである。あわせてintegrity候補 `114114` が変化した。

| Digitone表示音名 | Physical `21723` | Decoded record byte 2 |
|---|---:|---:|
| C4 | `0x30` | `0x30` |
| C5 | `0x3C` | `0x3C` |
| C#5 | `0x3D` | `0x3D` |
| D5 | `0x3E` | `0x3E` |

1半音の変更に対し保存値が1増減し、1オクターブの差が12であるため、Pitch fieldは半音単位の整数値として扱える。

## 注意：音名表記とMIDI番号

実験上、Digitone表示 `C5` が保存値 `0x3C`（decimal 60）となった。一般的なMIDIノート名称規約ではdecimal 60を `C4` と呼ぶ場合があるため、Harmony Cloudでは「表示音名」と「イベント内部のMIDI番号」のオクターブ規約を明示してから変換する必要がある。

## 仕様化できる範囲

```text
trigger_record.byte_2 = pitch_code
pitch_code increments by 1 per semitone
Digitone displayed C5 = 0x3C
```

有効音域の最小／最大、およびTrack 2以降については未検証である。
