# SLAM Working Branch - Summary of Changes

## Key Points
- Global rotation limit (angular_z ≤ 1.3 rad/s) in every Python script (wall_centering_node.py, teleop_keyboard.py).
- Special cases (frontal obstacle) fixed to avoid violent rotations.
- angular_z is saturated only at publication time.
- Single CSV log for the tests.
- LiDAR front calibration (-90°) applied.
- SLAM stack started without RViz to save CPU, then RViz started separately.

## Launch Procedure
1. Start the SLAM stack without RViz:
   ```bash
   ./start_slam_no_rviz.sh
   ```
2. Start RViz in another terminal:
   ```bash
   rviz2 -d rviz_config.rviz
   ```
3. Start the Python control script (e.g. wall_centering_node.py).

## Next step
- Test on the real track.
- Publish everything on the `slam-working` GitHub branch.

## Modified files
- wall_centering_node.py
- teleop_keyboard.py
- scan_restamper_simple.py
- README.md
- CMD_VEL_OPTIMAL_MAPPING.md

## Test history
- Stable mapping with angular_z = 1.3
- SLAM + RF2O stack validated
- CPU monitored during simultaneous tests

---
For more details, see the other MD files (CMD_VEL_OPTIMAL_MAPPING.md, MAPPING_ROTATION_FIX.md, RF2O_SETUP.md, etc.).
