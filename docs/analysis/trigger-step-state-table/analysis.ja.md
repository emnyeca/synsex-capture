# Trigger Track別 Step state table 解析結果

## 目的

Track別の Step state table について、Step番号に対する offset 変化を規則化する。

本系列では次の操作を比較した。

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

## 重複除外

取得レンジ `capture_20260525_115407_0019..0034` には、Step1周辺で誤取得が含まれていた。

- `0030` は `0028` と byte-identical（Track8 / Step1 の重複）
- `0031` は誤取得フロー由来の余分な BASE_EMPTY

この2件を除外し、14件の正規系列として再構成した。

## 正規化後の系列

`captures/Track_Step_State_Table/` に次を配置した。

- `1_Empty.syx`
- `2_Track2Step1C5Added.syx`
- `3_EmptyAfterTrack2Step1.syx`
- `4_Track2Step2C5Added.syx`
- `5_EmptyAfterTrack2Step2.syx`
- `6_Track2Step3C5Added.syx`
- `7_EmptyAfterTrack2Step3.syx`
- `8_Track2Step16C5Added.syx`
- `9_EmptyAfterTrack2Step16.syx`
- `10_Track8Step1C5Added.syx`
- `11_EmptyAfterTrack8Step1.syx`
- `12_Track8Step2C5Added.syx`
- `13_EmptyAfterTrack8Step2.syx`
- `14_Track8Step16C5Added.syx`

## 確定した観測

### 1. Trigger record 側は既知仕様どおり

- offset `21720`: 0-based track index
- offset `21721`: 0-based step index

Track 2 では `0x01` 固定、Track 8 では `0x07` 固定で、stepを変えると `21721` が `0x00`, `0x01`, `0x02`, `0x0F` と変化した。

### 2. Step state 側に Track別・Step別 triplet が存在

各 Add で、record領域に加えて Step state 側の3 offsetが変化した。

Track 2:

| Step | 変化offset (triplet) |
|---:|---:|
| 1 | 1370, 1372, 1373 |
| 2 | 1370, 1374, 1375 |
| 3 | 1370, 1376, 1377 |
| 16 | 1402, 1406, 1407 |

Track 8:

| Step | 変化offset (triplet) |
|---:|---:|
| 1 | 9506, 9511, 9512 |
| 2 | 9513, 9514, 9515 |
| 16 | 9545, 9546, 9547 |

### 3. BASE_EMPTY再インポート運用では Empty差分が0

`vs_step1_to_03/05/07/09/11/13` はすべて `difference_count: 0`。

前回の「削除後残留値」問題を避けるため、今回の再インポート運用は有効。

## 現時点の規則化

- Trigger record は `record[0]=track_index`, `record[1]=step_index` で確定。
- Step state は Trackごとにブロックが分かれ、Stepに応じた triplet が更新される。
- Step 1..3 では連続性が見えるが、Step16では非連続ジャンプが観測されるため、単純一次式のみでの一般化は未確定。

## 未確定

- Track 2 / Track 8 以外で同形の triplet 規則が成り立つか。
- Step 4..15 の完全な配置規則。
- triplet各byteの意味（mask/control/active flag 分離）。
