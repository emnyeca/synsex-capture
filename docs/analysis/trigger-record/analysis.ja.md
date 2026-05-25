# Trigger record / slot allocation 解析結果

## 目的

通常Triggerを追加・移動・削除したとき、Step存在情報とTrigger内容がどこへ格納されるか、また複数Triggerの格納順が何に依存するかを特定する。

## 実験系列

主に次の比較を用いた。

- TriggerをStep 1〜16へ単発で移動する系列
- TriggerをStep 1から順に追加する系列
- `Step 16 → Step 1` の順で追加する系列
- `Step 1 → Step 16 → Step 1削除 → Step 1再追加` の系列

## 確定した結果

### 1. Trigger内容は固定長slotとして保持される

7-bit unpack後のTrigger領域では、通常Triggerは6 byte固定長のrecordとして解釈できる。

```text
record = [track_index, step_index, pitch, velocity, length, field_5]
```

今回解析した通常Triggerでは、未編集属性を継承した `Step 1 / C5` は次のrecordになる。

```text
[00, 00, 3C, FF, FF, 00]
```

Track 1〜8 で `Step 1 / C5 / Velocity継承 / Length継承` を比較した結果、`field_0` は 0-based の Track index として確定した。

```text
Track 1 -> 0x00
Track 2 -> 0x01
Track 3 -> 0x02
Track 4 -> 0x03
Track 5 -> 0x04
Track 6 -> 0x05
Track 7 -> 0x06
Track 8 -> 0x07
```

このため Trigger record配列は Track 共通領域であり、各recordが自身の Track/Step/Pitch/Velocity/Length を保持するモデルが成立する。`field_5` は引き続き未確定。

### 2. slotはStep位置に固定されない

`Step 16 → Step 1` の順に追加した場合、recordは `Step 16`, `Step 1` の順に配置された。`Step 1 → Step 16` の順に追加した場合は逆順になった。

したがって、Trigger recordはStep昇順／降順で自動ソートされない。

### 3. 削除時にslotは前詰めされない

`slot 1 = Step 1`, `slot 2 = Step 16` の状態からStep 1を削除すると、`slot 1` が未使用になり、Step 16は `slot 2` に残った。

```text
before delete: slot 1 = Step 1, slot 2 = Step 16
after delete : slot 1 = empty,  slot 2 = Step 16
```

### 4. 再追加では空いている若いslotが再利用される

上記の状態へStep 1を再追加すると、空いていた `slot 1` が再利用され、削除前のslot配置へ戻った。

### 5. Step存在状態はrecordとは別領域にも保持される

Trigger追加時にはrecord領域に加え、ファイル前方のStep対応領域でも変化が発生する。Track 1で観測した例は以下。

| Step | Physical offset | 観測変化 |
|---:|---:|---|
| 1 | `16` | Trigger追加時にbit変化 |
| 2 | `19` | Trigger追加時にbit変化 |
| 3 | `21` | Trigger追加時にbit変化 |
| 4 | `23` | Trigger追加時にbit変化 |
| 5 | `25` | Trigger追加時にbit変化 |
| 6 | `28` | Trigger追加時にbit変化 |
| 12 | `41` | Trigger追加時にbit変化 |
| 13 | `44` | Trigger追加時にbit変化 |
| 16 | `51` | Trigger追加時にbit変化 |

この領域は Step state / Trigger presence 領域と扱う。Track 1〜8 / Step 1 では、次の active flag 候補 offset が確認できた。

| Track | active flag 候補 offset |
|---:|---:|
| 1 | `16` |
| 2 | `1373` |
| 3 | `2729` |
| 4 | `4086` |
| 5 | `5443` |
| 6 | `6799` |
| 7 | `8156` |
| 8 | `9512` |

また、追加時に変化した Step state 側 offset の一部は削除後も初期化情報として残る。したがって `EmptyAfterTrackN` は「Triggerが存在しない状態」ではあるが、`BASE_EMPTY` と完全一致ではない。

## 実装への含意

新規生成では、完成状態のTrigger群を決定的な任意順序で空きslotへ配置できる可能性が高い。ただし、既存SYXを編集して実機の編集履歴互換を保つ場合は、削除時に前詰めせず、最若空きslotを再利用する挙動を再現する必要がある。

現在のHarmony Cloud用途では、空テンプレートからの一括生成を前提とし、アプリ側で配置順を固定する設計が扱いやすい。

## 未確定事項

- `field_5` の意味
- Track 2〜8 の Step 2以降における Step state offset 規則
- Track 9以降の Track index / Step state 挙動
- Step state領域の一般的なoffset計算式
- Trigger slot領域の最大slot数
