# Optimal CMD_VEL for stable mapping (anti-drift)

This document summarises the most stable `cmd_vel` values to avoid drift when rotating and when moving.
Goal: smooth and reliable mapping, even if the robot is slow.

## 1) Recommended values (SAFE profile)

## Practical use
- Recommended linear motion: `linear.x = 0.10` to `0.14` m/s
- Recommended pure rotation: `angular.z = 1.30` rad/s
- Maximum tolerated rotation (avoid using it continuously): `angular.z = 1.50` rad/s
- Avoid abrupt setpoint changes (instant acceleration)

## Suggested SAFE profile
- `linear.x = 0.12` m/s
- `angular.z = 1.30` rad/s
- Duration of a 360° rotation at 1.30 rad/s: ~`4.83 s`

## Why this profile
- More stable than slow rotations that do not overcome friction
- Less aggressive than 1.5 rad/s, which can over-react
- Good accuracy/responsiveness trade-off for SLAM + RF2O

---

## 2) Rotation test results (history)

## `test_rotation_drift.py` test (old setting 1.0)
- Setpoint: rotation at `1.0` rad/s
- Measured result: `112.6°` (instead of 360°)
- Linear drift: `7.23 cm`
- Conclusion: **rotation too weak / friction / under-rotation**

## `test_rotation_drift.py` test (setting 1.5)
- Setpoint: rotation at `1.5` rad/s
- Measured result: `693.7°`
- Linear drift: `13.75 cm`
- Conclusion: **the robot turns, but over-reacts / rotation is over-estimated**

## Field feedback
- `1.3` rad/s in pure rotation: **works better**
- Recommendation: keep `1.3` for mapping (more stable)

---

## 3) Summary of the `diagnose_rotation.py` tests

The script compares the commanded rotation with the measured rotation (`/odom`).
Interpretation:
- Ratio < 40%: strong under-reaction (friction/slip, speed too low)
- Ratio 70-90%: correct with SLAM compensation
- Ratio > 120%: over-reaction/over-estimation (too aggressive)

With our trials:
- Low range (~1.0): under-reaction
- High range (~1.5): over-reaction
- **Practical target range: ~1.3 rad/s**

---

## 4) Good cmd_vel practices against drift

- Prefer constant commands (no fast pulses)
- When rotating, avoid `> 1.4` rad/s over long sequences
- Drive arcs (linear + moderate angular) rather than a long aggressive pivot
- Add a short pause (0.3-0.5 s) between phases: straight line -> rotation -> straight line
- Keep the surface as grippy as possible (less slipping)

---

## 5) Suggested presets

## Stable Mapping preset (recommended)
- `linear.x = 0.12`
- `angular.z = 1.30`

## Fine Rotation preset (tight areas)
- `linear.x = 0.08`
- `angular.z = 1.10`

## Fast preset (use sparingly)
- `linear.x = 0.15`
- `angular.z = 1.50` (short duration)

---

## 6) Check commands (during a test)

```bash
ros2 topic hz /scan
ros2 topic hz /odom
ros2 topic hz /map
ros2 topic hz /tf
```

Practical targets:
- `/odom`: stable, without gaps
- `/map`: continuous (does not need to be very high)
- No visible drift after a closed loop

---

## 7) Current final decision

For this robot and its motors:
- **Recommended rotation value: `1.3 rad/s`**
- **Recommended travel value: `0.12 m/s`**

If drift comes back:
1. lower the rotation to `1.2`
2. reduce the linear speed to `0.10`
3. avoid long rotations in place
