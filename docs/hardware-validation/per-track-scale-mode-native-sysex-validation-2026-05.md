# Digitone II Per Track Scale Mode Native SysEx Validation (2026-05)

## Status

- Hardware validation: pending
- Toolkit implementation: complete
- Authoritative mapping dataset: `datasets/analysis/per_track_field_mapping_t01_t16_20260529/summary.yaml`
- Validation fixture:
  - `examples/generated/per_track_scale_validation/per_track_signature.events.yaml`
  - `examples/generated/per_track_scale_validation/per_track_signature.syx`
  - `examples/generated/per_track_scale_validation/expected_values.yaml`

## On-device checklist

- Mode displays `Per Track`
- Track 1 LENGTH = `16`, SPEED = `1x`
- Track 2 LENGTH = `17`, SPEED = `1/2x`
- Track 3 LENGTH = `18`, SPEED = `1x`
- Track 4 LENGTH = `19`, SPEED = `1/2x`
- Track 5 LENGTH = `20`, SPEED = `1x`
- Track 6 LENGTH = `21`, SPEED = `1/2x`
- Track 7 LENGTH = `22`, SPEED = `1x`
- Track 8 LENGTH = `23`, SPEED = `1/2x`
- Track 9 LENGTH = `24`, SPEED = `1x`
- Track 10 LENGTH = `25`, SPEED = `1/2x`
- Track 11 LENGTH = `26`, SPEED = `1x`
- Track 12 LENGTH = `27`, SPEED = `1/2x`
- Track 13 LENGTH = `28`, SPEED = `1x`
- Track 14 LENGTH = `29`, SPEED = `1/2x`
- Track 15 LENGTH = `30`, SPEED = `1x`
- Track 16 LENGTH = `128`, SPEED = `1/2x`
- CHANGE displays `OFF`
- RESET displays `INF`
- CHANGE remains identical when inspecting different tracks
- RESET remains identical when inspecting different tracks

## Validation note

Do not mark this checklist as passed until the generated SysEx has been loaded on Digitone II and the displayed values have been verified manually.