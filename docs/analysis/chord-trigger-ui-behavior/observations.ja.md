# Digitone II Chord Trigger UI挙動観測結果 — Track 8 和音生成解析前整理

## スコープ

- Device: Digitone II
- Target track for future encoder use: Track 8
- Purpose: use one trigger containing multiple notes as a chord-progression track for EUB Changes
- Current stage: UI behavior observation before SysEx field analysis

既存の通常Trigger解析では、Track 8を含む単音Triggerについて標準的なtrigger record modelがすでに確認されている。本書は、その上に追加で存在する multi-note / chord-trigger UI挙動を整理するものであり、和音ノートが SysEx 上でどのように保存されるかはまだ確定しない。通常Trigger側の前提は `docs/analysis/trigger-record/analysis.ja.md` を参照する。

## 1. Hardware-observed UI behavior

### 1.1 Multi-note capacity

- One step can contain up to 16 notes.
- Each note inside one trigger can be edited individually.

### 1.2 Per-note editable parameters

各noteで観測できた編集項目は以下。

`NOTE`

- range: C0 to G10

`TIME`

- meaning: MICRO TIMING
- range: -23 to +23
- default: 0

`LEN`

- range: .125 to 128, INF

`VEL`

- range: 1 to 127

本書では、これらの binary encoding は一切推定しない。

### 1.3 代表 NOTE

本書では、UI上で trigger-level parameter display に表示されている note を `代表 NOTE` と呼ぶ。

定義:

`代表 NOTE`:
その時点で trigger-level parameter display を通じて NOTE / TIME / LEN / VEL が表示・操作される note。

重要事項:

- 代表 NOTE は hardware-observed UI concept である。
- それが固定 SysEx slot に対応するのか、可変 anchor field なのか、あるいは派生 selection rule なのかは未確定である。

### 1.4 Representative NOTE behavior: confirmed observations

#### 1.4.1 Initial representative selection when TIME is equal

観測事実:

- When multiple notes all have TIME = 0, the note added first is shown as the representative NOTE.

例:

```text
Add C5 first, then E5, both TIME = 0
→ Trigger displays C5 parameters.
```

#### 1.4.2 Representative change caused by earlier MICRO TIMING

観測事実:

- If a later-added note is edited so that its TIME is earlier than the current representative NOTE, that edited note becomes the representative NOTE.

例:

```text
C5 added first: TIME = 0
D5 added later: TIME = 0
→ Representative = C5

Edit D5 TIME to -1
→ Representative = D5
```

#### 1.4.3 Representative can revert when timing becomes equal again in the observed test

観測事実:

- In the observed test case, after D5 becomes representative by being moved earlier, restoring D5 TIME from -1 back to 0 returns the representative to the originally earlier-added C5.

例:

```text
C5 added first: TIME = 0
D5 added later: TIME = 0
→ Representative = C5

D5 TIME: 0 -> -1
→ Representative = D5

D5 TIME: -1 -> 0
→ Representative = C5
```

この時点で確定できるのは、代表 NOTE の選択規則が TIME 編集で変化し得ることと、その完全な状態遷移規則がまだ未確定であることだけである。厳密な内部規則は、今後の UI追加実験と SysEx解析が終わるまで未確定と扱う。

#### 1.4.4 Representative deletion

観測事実:

- Deleting the current representative NOTE causes the trigger display to move to a remaining representative NOTE.
- If TIME values are equal, the remaining note that was added earlier is shown.
- Re-adding the deleted original note afterward does not restore it as representative when the existing representative remains valid at the same TIME.

例:

```text
Create C5, E5, G5 with equal TIME.
Representative = C5.

Delete C5.
→ Representative = E5.

Re-add C5 at equal TIME.
→ Representative remains E5.
```

### 1.5 Trigger NOTE versus per-note NOTE editing

#### 1.5.1 Trigger-level NOTE edit

観測事実:

- Editing the trigger-level NOTE transposes the entire chord by the same interval.

例:

```text
Chord:
C5 E5 G5

Edit trigger NOTE:
C5 -> D5

Result:
D5 F#5 A5
```

境界挙動:

- Trigger NOTE cannot be moved further if any note in the chord would exceed the supported NOTE range C0 to G10.

#### 1.5.2 Individual representative NOTE edit

観測事実:

- Editing the NOTE value of the currently representative note in the per-note editor changes only that note, not the entire chord.

例:

```text
Chord:
C5 E5 G5

Edit representative note C5 individually:
C5 -> D5

Result:
D5 E5 G5

Trigger display:
D5, because the edited representative note is now D5.
```

#### 1.5.3 Trigger transpose after representative changed by TIME

観測事実:

- If TIME editing has changed the representative NOTE, trigger-level NOTE editing uses the currently displayed representative as the trigger-level anchor and transposes all notes by the same interval.

例:

```text
Initial chord:
C5 TIME=0
D5 TIME=-1
G5 TIME=0

Representative:
D5

Edit trigger NOTE:
D5 -> E5

Result:
D5 E5 A5

TIME relation remains:
0, -1, 0

Representative:
E5
```

この UI挙動だけから、SysEx が absolute note を保存するのか、interval を保存するのかは結論しない。

### 1.6 TIME / MICRO TIMING behavior

観測事実:

- TIME is MICRO TIMING.
- There is no Track Default TIME concept.
- A newly created trigger or newly added note begins with TIME = 0.
- Each note can hold its own TIME value.
- Editing trigger-level TIME moves all notes' TIME values together.
- TIME saturates at -23 and +23.
- Changing a note's TIME can change which note is representative.
- When the representative changes, the trigger display changes to that note's NOTE / TIME / LEN / VEL parameters.

初期 EUB Changes v1 policy:

- All generated chord-trigger notes use TIME = 0.
- Non-zero microtiming is not part of initial chord generation support.

### 1.7 LEN behavior

観測事実:

- LEN can be edited per note.
- When a trigger is in LEN inherit state, added notes behave as inherited LEN.
- When trigger LEN is explicit, newly added notes receive the representative NOTE's explicit LEN.
- If any note LEN is individually changed, the trigger becomes explicit rather than inherited.
- The trigger display shows the LEN of the current representative NOTE.
- Once explicit, note LEN values are independent from Track Default LEN.
- Editing trigger-level LEN applies the same relative parameter movement to all notes.
- Values saturate below minimum at `.125` and above maximum at `INF`.
- Saturation does not destroy the relative editing state. One step back from the boundary moves a saturated note one step back from that boundary.

例:

```text
INF -> 128
.125 -> .188
```

追加時挙動:

- If notes already have different LEN values and a new note is added, the new note receives the current representative NOTE's LEN value.

これは UI上の creation behavior としてのみ記録する。EUB Changes は完成済み final chord state を直接生成する前提であり、live add sequence 自体を再現する必要はまだない。

### 1.8 VEL behavior

観測事実:

- VEL can be edited per note.
- When trigger VEL is inherited, newly added notes behave as inherited VEL in the UI. Whether this is stored as per-note inherit or resolved internally is not yet known.
- When trigger VEL is explicit, newly added notes receive the representative NOTE's explicit VEL.
- If any note VEL is individually changed, the trigger behaves as explicit.
- The trigger display shows the VEL of the current representative NOTE.
- Editing trigger-level VEL applies the same delta to all note VEL values.
- VEL saturates at 1 and 127.
- After saturation, moving the trigger VEL control one step back also moves the saturated note back by one step.

例:

```text
C5 VEL = 70
E5 VEL = 50
G5 VEL = 127

Raise trigger VEL by 1:
C5 = 71
E5 = 51
G5 = 127

Move trigger VEL down by 1:
C5 = 70
E5 = 50
G5 = 126
```

追加時挙動:

- If notes already have different VEL values and a new note is added, the new note receives the current representative NOTE's VEL value.

例:

```text
C5 VEL = 70 and is representative
E5 VEL = 50
Add G5 at equal TIME
→ G5 VEL = 70
```

## 2. Working interpretation for future SysEx analysis

本節は実機 UI観測を踏まえた作業仮説であり、confirmed SysEx specification ではない。

- Chord trigger には通常Triggerの単音 record を超える追加状態が存在する可能性が高い。
- 代表 NOTE は単なる「最も早い note」のような stateless sorting rule だけでは説明できない。
- trigger-level NOTE/TIME/LEN/VEL 編集は、現在 UI に表示されている representative context を基準に和音全体へ作用している可能性がある。
- note追加時に representative NOTE の LEN / VEL が複製される挙動は、UI creation path 特有の copy rule を示している可能性がある。
- UI上の inherited / explicit 切替は、保存時に per-note marker として表現される可能性も、別の shared state として表現される可能性もある。

ここでの目的は、今後の raw SysEx diff を読む際に「何を区別して比較しなければならないか」を明確化することであり、内部保存モデルを確定することではない。

## 3. EUB Changes v1 生成方針案

これは product-generation policy であり、confirmed hardware storage fact ではない。

目的:

- Use Track 8 as an experimental/generated chord-progression track.
- Provide compact chord editing and performance operation inside Digitone II.

初期スコープ:

- Up to 6 generated chord notes per trigger.
- Source notes are the bounded chord voicing already produced by Changes.
- All generated note TIME values are 0.
- Notes are emitted in ascending pitch order.
- Because TIME is equal and the lowest note is emitted first, the displayed representative NOTE is normally the chord's lowest note.
- LEN is written explicitly and identically for all notes in the generated chord.
- VEL is written explicitly per note to create chord balance inside one track.

velocity 解釈の変更点:

Existing six-track chord-cloud output:

- Track Default Velocity acts as moving voice-layer balance.

Track 8 single-trigger chord output:

- Per-note explicit VEL defines vertical chord balance within a single track.
- VEL assignment is based on the sorted chord voicing / audible role rather than preserving old moving-track identity.

初期候補の per-note VEL profile は、6-note chord を低音から高音へ並べて次を想定する。

```text
70, 70, 70, 50, 70, 50
```

これは Initial listening-test candidate であり、まだ最終的な musical balance ではない。

また、Track 8 chord output は、既存の Track 1〜6 distributed chord-cloud output と hardware listening test で比較するまでは experimental / optional output mode として扱う。

## 4. 未確定事項

- How chord-note data is represented in SysEx:
  - absolute note values
  - representative note plus intervals
  - or another compound representation
- Whether representative NOTE state is stored explicitly in SysEx or derived from chord-note records plus editing history/state.
- The complete state-transition rule for representative NOTE when:
  - the current representative TIME is moved later than another existing note
  - multiple notes tie after prior representative changes
  - notes with earlier/later TIME are deleted or added
- Whether inherited LEN / VEL are stored as inherit markers for every note or are represented through another shared state.
- The binary storage fields for per-note:
  - NOTE
  - TIME
  - LEN
  - VEL
- Whether the UI's saturation/backtracking behavior is represented in saved SysEx state or exists only during live editing.

## 5. Planned Phase 1 SysEx capture sequence

この節は capture plan であり、以下の `.syx` がすでに存在するとは主張しない。

推奨 raw capture folder:

```text
captures/Track08_Chord_Trigger_Notes_20260529/
```

推奨 future analysis folder:

```text
datasets/analysis/track08_chord_trigger_notes_20260529/
```

### 5.1 Baseline / increasing note count

```text
01_EMPTY_PATTERN.syx
02_T08_S01_C5_SINGLE_NOTE.syx
03_T08_S01_CHORD_02_C5_E5.syx
04_T08_S01_CHORD_03_C5_E5_G5.syx
05_T08_S01_CHORD_04_C5_E5_G5_B5.syx
06_T08_S01_CHORD_05_C5_E5_G5_B5_D6.syx
07_T08_S01_CHORD_06_C5_E5_G5_B5_D6_A6.syx
```

### 5.2 NOTE storage model: direct creation versus trigger transpose

```text
08_DIRECT_D5_FS5_A5.syx
09_TRANSPOSED_C5_E5_G5_TO_D5_FS5_A5.syx
```

内容:

`08`

- Directly create D5 F#5 A5.

`09`

- Create C5 E5 G5.
- Use trigger-level NOTE edit to transpose the complete chord to D5 F#5 A5.

目的:

- Determine whether identical final sounding notes produce identical saved data, or whether trigger transposition leaves a distinct chord representation.

### 5.3 Input order at equal TIME

```text
10_ORDER_C5_THEN_E5_TIME0.syx
11_ORDER_E5_THEN_C5_TIME0.syx
```

### 5.4 Representative NOTE update caused by TIME

```text
12_REPRESENTATIVE_C5_E5_TIME0.syx
13_REPRESENTATIVE_E5_TIME_MINUS1.syx
14_REPRESENTATIVE_E5_RETURN_TIME0.syx
```

capture log に残すべき UI補足:

`12`

- C5 added before E5.
- Both TIME = 0.
- UI representative = C5.

`13`

- Edit E5 TIME to -1.
- UI representative = E5.

`14`

- Edit E5 TIME back to 0.
- UI representative = C5.

### 5.5 Multiple chord triggers / binding behavior

```text
15_TWO_CHORDS_S01_THEN_S05.syx
16_TWO_CHORDS_S05_THEN_S01.syx
```

内容:

- Step 1: C5 E5 G5
- Step 5: D5 F#5 A5

`15`

- Create Step 1 chord first, then Step 5 chord.

`16`

- Create Step 5 chord first, then Step 1 chord.

目的:

- Determine whether chord-note extension data follows ordinary trigger slot creation order or is stored by Track/Step location.

### 5.6 Optional maximum-capacity capture

```text
17_T08_S01_CHORD_16_NOTES.syx
```

これは optional であり、initial six-note EUB Changes implementation のための必須 capture ではない。

## 6. Capture log template

template file:

```text
docs/analysis/chord-trigger-ui-behavior/capture-notes-template.yaml
```

目的:

- Raw SysEx diff alone cannot recover all UI-observed representative state, so each capture must be accompanied by a manual UI observation record.
