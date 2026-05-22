# Digitone II Pattern SysEx 解析ガイド（必要部分のみ書き換え）

この手順は「完全解析」ではなく、Harmony Cloudに必要な要素だけを安全に特定して書き換えることを目的にします。

## 目的とスコープ

優先して扱う項目:

- 必須: Track 1〜6 の Trig 有無
- 必須: 各 Trig の Note
- 必須: 各 Trig の LEN
- 高: 各 Trig の Velocity

後回しにする項目:

- Pattern LENGTH
- Pattern SPEED
- FX / LFO / Micro Timing

変更しない項目:

- Sound / Synth Parameter

## 前提

- Digitone II 上に、Harmony Cloud用音色を配置したテンプレート Pattern を作成済み
- テンプレート Pattern の SysEx を取得できる
- このリポジトリの GUI を利用できる

起動コマンド:

```bash
synsex_capture gui
```

```powershell
python -m synsex_capture gui
```

今すぐ起動するコマンド:

```powershell
cd D:\emnye\Documents\GitHub\synsex-capture
.\.venv\Scripts\python.exe -m synsex_capture gui
```

## GUIでの解析フロー

### 1. 空テンプレートを取得

1. Digitone II でテンプレート Pattern を保存
2. SysEx Dump を取得して `template_empty.syx` として保存

### 2. 1項目だけ変更したダンプを作る

1. Digitone II 上で、1つの操作だけ変更
2. 例: Track 2 / Step 5 の Note を1つ上げる
3. SysEx Dump を `change_note_t2s5.syx` として保存

### 3. Diff & Mapping タブで差分抽出

1. `Template / Before .syx` に `template_empty.syx`
2. `Changed / After .syx` に `change_note_t2s5.syx`
3. `Run Diff` を実行
4. 差分オフセット一覧を確認（offset / before / after）

ポイント:

- 1回の実験で変更は1項目だけにする
- 同様の手順で Note / LEN / Velocity / Trig ON/OFF を個別に採取

### 4. Patch YAMLを出力して知見を蓄積

1. `Export Patch YAML` を押下
2. 例: `datasets/patches_note_t2s5.yaml` として保存

YAML は以下形式:

```yaml
patches:
  - offset: 1234
    before: 0x2A
    value: 0x30
```

このファイルを「操作とオフセットの対応表」として育てます。

### 5. Hex Viewer タブで周辺確認

1. 対象 `.syx` を選択
2. `View Hex` でオフセット周辺の連続性を確認

用途:

- 7bit packing やチェックサム位置の目視補助
- 連続するステップデータ領域の探索

### 6. Selective Patch タブで部分書き換え

1. `Template .syx` に元テンプレートを指定
2. `Patch YAML` に差分YAMLを指定
3. `Output .syx` を指定
4. `Apply Patch` を実行

この操作は、指定オフセットだけを書き換えます。

### 7. 再送信して実機検証

生成した `.syx` を以下で再送:

```bash
synsex_capture replay --out-port 1 --file captures/patched.syx
```

Digitone II 上で Note / LEN / Velocity / Trig の反映を確認します。

## 推奨の実験順

1. Trig ON/OFF
2. Note
3. LEN
4. Velocity
5. Pattern LENGTH / SPEED（必要になってから）

## 解析記録テンプレート

`datasets/` 配下に、以下のようなメモYAMLを併設すると再現性が上がります。

```yaml
experiment: note_change_t2s5
before_file: captures/template_empty.syx
after_file: captures/change_note_t2s5.syx
operation_on_device: "Track2 Step5 Note +1"
candidate_offsets:
  - 1234
  - 1235
notes: "offset 1234 がノート値本体の可能性"
```

## 注意点

- 本方式は「必要バイトのみ編集」前提です。全パラメータの完全逆コンパイルは目的外です。
- 同時に複数項目を変更すると、差分対応付けが困難になります。
- `before` 値付きのパッチを使うと、誤ったテンプレートへの適用を検知できます。
