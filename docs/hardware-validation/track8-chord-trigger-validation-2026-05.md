# Track 8 Chord Trigger Validation (2026-05)

Validated Track 8 chord-trigger storage model for Digitone II ordinary trigger records.

Confirmed storage model:

- A chord trigger is represented as multiple ordinary trigger records sharing the same Track and Step.
- Track 8 uses `track_index_0based = 7`.
- NOTE stores absolute MIDI pitch.
- VEL stores per-note explicit velocity or inherit marker.
- LEN stores per-note explicit length code or inherit marker.
- TIME stores signed micro-timing in the ordinary trigger record byte.

Authoritative capture and analysis sources:

- `captures/Track08_Chord_Trigger_Notes_20260529/`
- `datasets/analysis/track08_chord_trigger_notes_20260529/track08_chord_trigger_notes_confirmed.yaml`

Toolkit schema/export updates validated in this feature:

- `events[].time` accepts `-23..23` and encodes signed int8 two's-complement.
- Duplicate Track/Step records are permitted for Track 8 when note values remain distinct.
- Track 8 chord notes continue to use the ordinary six-byte trigger record encoder.

Generated validation fixtures:

- `examples/generated/track8_chord_trigger_validation/track8_cmaj7_root.events.yaml`
- `examples/generated/track8_chord_trigger_validation/track8_cmaj7_root.syx`