# PATTERN総STEP変更とTrigger表示・拡張複製の観測

## 位置づけ

本項目は、実機UI上で既存Triggerを含むPATTERNの総STEPを変更したときの挙動を記録する。Harmony Cloudは完成状態のSYXを一括生成するため、この操作履歴互換を生成ロジックの要件とはしない。

## 実験系列

```text
Step 1 / C5 Triggerあり、PATTERN-wide、総STEP16
→ 総STEP64
→ 総STEP16へ戻す
→ Step 16にTrigger追加
→ 総STEP15（Step 16が範囲外）
→ 総STEP16（Step 16が再び範囲内）
```

## 確定した結果

### 1. 縮小で範囲外になるTriggerは削除されない

Step 16 Triggerが存在する状態で総STEPを16から15へ縮小すると、実機画面上ではStep 16 Triggerが非表示になった。しかし、Step 16 Triggerに対応する既知のrecord/state offsetは変化しなかった。

総STEPを15から16へ戻すと、Step 16 Triggerが再表示され、縮小前後の表示中状態はbyte-identicalだった。

```text
総STEP縮小 = 範囲外Triggerの非表示化
総STEP再拡張 = 保持されていたTriggerの再表示
```

### 2. 既存Triggerを含む状態で総STEPを拡張すると追加Trigger相当データが生じる

Step 1 / C5のみを持つ総STEP16の状態から総STEP64へ拡張した比較では、総STEPfield以外に、Step 17 / 33 / 49 に対応すると解釈できる通常Trigger record形式の差分が生じ、64から16へ戻しても残存した。

実機上の追加確認により、総ステップが `16 * n` のとき、step `a` に書き込まれたTriggerは、総ステップ延長時に少なくとも `a + 16 * n` の位置へ拡張複製される挙動が確認された。

操作順や延長幅による詳細な反復規則は、Harmony Cloud用途では追跡しない。

## Harmony Cloudへの結論

Harmony Cloudでは、総STEP変更を実機の逐次編集操作として模倣しない。生成順は次で固定する。

```text
1. PATTERN-wide modeを設定
2. PATTERN総STEPを最終値に設定
3. Tempo / SPEED / Track既定値を設定
4. 生成対象のTriggerだけを配置
5. integrity / checksumを更新
```

既存Triggerを書き込んだ後で総STEPを拡張する生成処理は避ける。
