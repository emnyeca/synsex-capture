# PATTERN NAME 解析結果

## 目的

Digitone II Pattern Name の保存位置、文字制約、短い名前のpadding規則を特定し、`digitone-syx-toolkit` が安全に書き込める実装条件を確定する。

## 確定した結果

1. Name は decoded payload 上で2箇所にミラー保存される。
2. primary は `88788..88803`、shadow は `89096..89111`（各16 byte）。
3. 短い名前の残りは space ではなく `0x00` でpaddingされる。
4. primary と shadow は全ケースで一致した。
5. 拡張文字連続ケース `ÅÄÖÜßÆØÇÑ` は `C5 C4 D6 DC DF C6 D8 C7 D1` で保持された。

## Space保持の実測（cases 008/009/010）

実機UI観測どおり、leading/trailing/internal spaceはtrimされない。decoded 16-byteは次のとおり。

1. case 008 (`"               A"`):
   `20 20 20 20 20 20 20 20 20 20 20 20 20 20 20 41`
2. case 009 (`"A               "`):
   `41 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00`
3. case 010 (`"       A        "`):
   `20 20 20 20 20 20 20 41 00 00 00 00 00 00 00 00`

補足: case 009/010のtrailing領域はspaceではなくnull padding (`0x00`)。

## 実装ポリシー

1. 入力正規化は ASCII 小文字のみを大文字化する（`a-z -> A-Z`）。
2. 長さは正規化後16文字以下を許可する。
3. 文字集合は実機確認済み集合のみ許可する。
4. 書き込みは primary/shadow の両方へ同一16 byteを書き込む。
5. 16 byte未満は `0x00` padding を適用する。

## 補足

- 物理差分比較では 7-bit packing の制御byteも変化し得る。特に `0x80+` 文字では control byte の変化は期待挙動である。
- Bundle連結時の受信順序・命名運用は本解析の対象外。

将来実装向けに確認済みの受信挙動:

- 複数Pattern SYXは連続受信できる。
- 配置先は受信開始時に実機で選んだ開始slotから順次決まる。
- 送信元slot情報は配置先決定に使われない。
- 同一配置先へ受信すると上書きされる。
- よって将来のPattern Bundle生成で配置先slot情報の埋め込みは不要。
