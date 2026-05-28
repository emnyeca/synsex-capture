# Track Default Velocity Hardware Validation (Jazz Cloud Profile)

## Objective

Validate that pattern-level Track Default Velocity writes are reflected on device while trigger-level inherit behavior remains intact.

## Validation Files

- YAML: examples/generated/track_default_velocity_validation/jazz_cloud_velocity_profile.digitone.events.yaml
- SYX: examples/generated/track_default_velocity_validation/jazz_cloud_velocity_profile.syx

## Expected Profile

- Track 1: 50
- Track 2-6: 70
- Track 7: 100
- Trigger rows in YAML remain `velocity: inherit`

## Procedure

1. Send the generated SYX to Digitone II.
2. Open the target pattern and inspect Track default velocity values.
3. Confirm Tracks 1..7 values match expected profile.
4. Inspect placed triggers and confirm they show inherit state (not explicit per-trigger value).
5. Change Track 1 default velocity and verify inherited triggers follow the new default.
6. Edit one trigger to explicit velocity, then change Track 1 default again and confirm explicit trigger does not change.

## Pass Criteria

- Track defaults match expected values after load.
- Inherited triggers remain inherit markers.
- Explicit trigger velocity remains explicit after track default changes.
