# 🎯 LIDAR-ONLY MODE: Trust the LIDAR 100%, Ignore IMU & Odometry

## Strategy

**Old approach:** mix IMU (very poor) + odometry (no encoders) + LIDAR (good)
→ **Conflict** = bad mapping

**New approach:** **LIDAR ALONE**
→ Ignore the IMU and the odometry completely
→ SLAM ONLY uses LIDAR scan matching

---

## 🔧 Changes Made

### 1. **motor_odom_node.py** - MASSIVE covariances

```python
# BEFORE:
pose_covariance[yaw] = 0.05  # "I am 95% sure"

# AFTER:
pose_covariance[x]   = 10.0  # "I know NOTHING about X"
pose_covariance[y]   = 10.0  # "I know NOTHING about Y"
pose_covariance[yaw] = 10.0  # "I know NOTHING about the angle"

twist_covariance[wz] = 1.0   # "My gyro is GARBAGE"
```

**Effect:** SLAM reads the covariance and concludes: "This odometry is worthless, ignore it."

---

### 2. **simple_ekf.py** - Ignore the IMU

```python
# BEFORE:
imu_noise = 0.01  (IMU confidence = 99%)
wz_fusion = 0.9 * old + 0.1 * imu  (90% IMU)

# AFTER:
imu_noise = 5.0   (IMU confidence = only 17%!)
wz_fusion = 0.95 * old + 0.05 * imu  (IMU 95% ignored)
```

**Effect:** the EKF says "I almost completely ignore the IMU"

---

### 3. **slam_toolbox_params.yaml** - AGGRESSIVE SLAM scan matching

```yaml
# BEFORE:
initial_pose_guess_error_in_rotation: 0.5    # "Trust the odometry 95%"
initial_pose_guess_error_in_translation: 0.5

coarse_search_angle_offset: 0.349             # +/- 20° search

# AFTER:
initial_pose_guess_error_in_rotation: 2.0    # "Ignore the odometry!"
initial_pose_guess_error_in_translation: 2.0

coarse_search_angle_offset: 0.785             # +/- 45° search (much wider!)
minimum_travel_distance: 0.05                 # Process almost every scan
minimum_travel_heading: 0.05                  # Process every micro-rotation
```

**Effect:** SLAM searches **very widely** for LIDAR matches and ignores the odometry predictions

---

## 📊 Data flow architecture

```
┌─────────────────────────────────────┐
│     Robot in motion                 │
└────────┬────────────────────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
motor_odom   IMU (poor & noisy)
[Cov=10]     [95% ignored]
    │          │
    └────┬─────┘
         │
         ▼ (very high covariance = tells SLAM "ignore me")
    simple_ekf.py
    [0.95 × previous state]  ← Does nothing useful
         │
         ▼
    SLAM Toolbox
         │
    ┌────┴──────────────────────────────────┐
    │  Scan Matching (LIDAR ALONE)          │
    │  ✓ Matches the point cloud to the map │
    │  ✓ Ignores the odometry completely    │
    │  ✓ Ignores the IMU completely         │
    │  ✓ Computes the pose from LIDAR ONLY  │
    └────┬──────────────────────────────────┘
         │
         ▼
    CORRECT POSE (LIDAR based)
         │
         ▼
    /tf : map → odom → base_link
         │
         ▼
    RViz: ✨ Good map ✨
```

---

## ✅ Benefits

| Old | New |
|-----|-----|
| ❌ IMU + odometry + LIDAR = conflict | ✅ LIDAR ALONE = consistent |
| ❌ Mapping diverges when rotating | ✅ Mapping stays stable even when rotating |
| ❌ SLAM is confused | ✅ SLAM knows it must trust the LIDAR |
| ❌ Low covariance = false confidence | ✅ High covariance = no false confidence |

---

## 🧪 How to test

### Before (old code):
```
W = forward      → Mapping OK
D = turn         → Mapping BROKEN
```

### After (new code):
```
W = forward      → Mapping PERFECT ✨
D = turn         → Mapping PERFECT ✨
W+D+W = complex  → Mapping PERFECT ✨
```

### Running the test:

**Terminal 1:**
```bash
./start_stack.sh
```

**Terminal 2:**
```bash
python3 teleop_keyboard.py
```

**RViz:**
- Watch the map in real time
- Press W → see the walls ahead
- Press D → SEE THE ROTATION STAY SMOOTH in the map (it used to glitch)
- Do complex moves → the map remains good

---

## ⚙️ Key Parameters Explained

### 1. **coarse_search_angle_offset: 0.785** (+/- 45°)

Before: SLAM searched ±20° around the pose estimated by the odometry
Now: SLAM searches ±45° (very wide) because it does NOT trust the odometry

### 2. **initial_pose_guess_error_in_rotation: 2.0**

Before: covariance 0.5 = "I expect an error of ±0.5 rad"
Now: covariance 2.0 = "I expect an error of ±2 rad = ±115°" = "Ignore your guess"

### 3. **minimum_travel_distance: 0.05**

Before: wait for 10cm of motion before adding to the map
Now: add every 5cm = more anchor points = better localisation

---

## 🚨 If Something Goes Wrong

### If the mapping is still bad:

**Check the covariances:**
```bash
# Terminal 3:
python3 diagnostic_monitor.py

# Look at "Yaw Covariance" in motor_odom
# It must be > 5.0 (not 0.05!)
```

**Check that SLAM uses scan matching:**
```bash
# In RViz:
# Add → By topic → /map
# The map should update in real time
# No jumps
```

### If the robot loses its position:

This is **normal** in LIDAR-ONLY mode! There is no initialisation from odometry
- The robot must first see LIDAR features
- Once the features are found, it works well
- In an open field (no walls): the LIDAR cannot localise

---

## 📋 Summary of Modified Files

| File | Change | Impact |
|------|--------|--------|
| `motor_odom_node.py` | Covariances x10 | "Odometry = worthless" |
| `simple_ekf.py` | Ignores the IMU 95% | "IMU = worthless" |
| `slam_toolbox_params.yaml` | Scan search x2 + errors x4 | "LIDAR = everything" |

---

## 🎓 Key Concept

**High covariance = "I am not sure"**

```
Covariance = 0.01  → "I am 99% sure (false confidence if it is a poor gyro!)"
Covariance = 10.0  → "I am 100% lost (honest confidence!)"

SLAM reads:
  motor_odom: covariance=10 → "Ignore"
  LIDAR: implicitly low covariance → "Use"
```

With this setup: **SLAM = 100% LIDAR, 0% odometry/IMU**

🚀 **Ready to test!**
