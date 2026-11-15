# 🔍 FULL AUDIT - SAFETY AND PERFORMANCE

**Date**: 16 Feb 2026  
**Problem**: the robot "drives straight into the wall", mapping is awful while rotating

---

## 📊 EXECUTIVE SUMMARY

| Component | Problem | Severity | Fix |
|-----------|---------|----------|-----|
| **d_stop** | 0.25m is TOO small | 🔴 **CRITICAL** | → 0.35m |
| **d_slow** | 0.60m not progressive enough | 🔴 **CRITICAL** | → 0.80m |
| **w_max** | 2.5 rad/s (143°/s) | 🔴 **CRITICAL** | → 0.5 rad/s max |
| **kp** | 2.0 too aggressive | 🟠 **HIGH** | → 0.8 |
| **minimum_travel_heading** | 0.1 rad too small | 🟠 **HIGH** | → 0.15 rad |
| **emergency_hold_time** | 0.35s too short | 🟠 **HIGH** | → 0.8s |
| **Front safety zone** | front_half_deg=10° | 🟡 **MEDIUM** | → 15° |

---

## 🔴 CRITICAL #1: Stopping distance too short

### Problem:
```
d_stop = 0.25m = 25cm

Typical reaction time @ 0.6 m/s:
  - SLAM: 100-200ms
  - Wall-follow loop: 100ms
  - Motor: 50ms
  = At least 250ms in total = 15cm of drift
  
The robot stops at 25cm but has already moved 15cm since the detection!
```

### Why it is dangerous:
- At 60 cm/s, the robot covers **6cm per 100ms**
- Obstacle detected → 100ms → the robot has moved 6cm
- Obstacle detected at 25cm → the robot is already at 19cm
- 1-2 more cycles and it is a COLLISION

### Fix:
```yaml
d_stop:  0.35m  # Instead of 0.25m (+40cm of buffer)
d_slow:  0.80m  # Instead of 0.60m (more progressive)
```

This gives:
- **350mm of safety stop** (realistic given the delay)
- **800mm of progressive slow-down** (smooth)

---

## 🔴 CRITICAL #2: w_max = 2.5 rad/s IS A TIME BOMB

### Impact calculation:
```
w_max = 2.5 rad/s
    = 2.5 × (180/π) deg/s
    = 143°/s  ← EXTREME

At 10Hz (SLAM publish rate):
    143° / 10 = 14.3°/frame
    
SLAM parameter: minimum_travel_heading = 0.1 rad = 5.7°
So SLAM records a pose every 5.7°, but it receives 14.3° per frame!
    = 14.3° / 5.7° = 2.5 frames skipped between two SLAM poses!
    
= DISCONTINUOUS MAPPING, wrong estimated pose
```

### Comparison:
```
Current version (v2):
  w_max = 2.5 rad/s = 143°/s → SLAM LOSES THE POSE

Standard ROS2:
  max_angular_vel = 1.5 rad/s (nav2_params) = 86°/s

Real mobile robots:
  Turtlebot3: max 2.84 rad/s (but it has encoders!)
  Lidar-only robots: 0.3-0.8 rad/s (no reliable odometry)
```

### Fix:
```python
# Limit the angular speed DRASTICALLY
w_max = 0.50  # rad/s = 28°/s
          # SLAM sees: 28° / 5.7° = 4.9 poses/sec = CONTINUOUS!

# In an emergency, use the real w_max:
w_emergency = 1.0  # rad/s = 57°/s (only to get away)
```

---

## 🟠 HIGH: Unstable PID

### Problem:
```python
kp = 2.0   # Huge proportional gain
kd = 0.4   # Weak derivative
```

**Example of an unstable scenario:**
- Robot very close to the wall (d = 0.1m)
- d_ref = 0.45m
- Error: e = 0.45 - 0.1 = 0.35m ← MASSIVE
- w = kp × e = 2.0 × 0.35 = **0.7 rad/s** (straight away!)
- With w_max=2.5, clamped to 2.5 → chaotic rotation
- Then suddenly close to the opposite wall
- Same calculations the other way round
- **WILD OSCILLATION**

### Fix:
```python
kp = 0.8   # Less aggressive
kd = 0.6   # Better derivative
```

---

## 🟠 HIGH: Minimum travel heading too permissive

### Problem:
```yaml
minimum_travel_heading: 0.1  # rad = 5.7°

With w_max = 2.5 rad/s and SLAM @ 10Hz:
  Rotation per frame = 2.5 / 10 = 0.25 rad = 14.3°
  
SLAM expects 5.7° but the robot turns 14.3° per frame
= Several frames "skipped" by SLAM
= Sparse map, the pose is "jumping"
```

### Fix:
```yaml
minimum_travel_heading: 0.15  # rad = 8.6°
  # With w_max=0.5: 0.5/10 = 0.05 rad = 2.9°
  # SLAM sees: 2.9° < 8.6° → no update → OK
  # When it updates: nicely continuous
```

---

## 🟠 HIGH: Emergency latch too short

### Problem:
```python
emergency_hold_time = 0.35  # seconds

At 60 cm/s, the robot can travel 21cm in 350ms!
If detected at d_stop=0.25m, it is already in the wall within 2 cycles!
```

### Fix:
```python
emergency_hold_time = 0.8  # seconds
  # Gives 48cm of drift protection
  # At 0.5 rad/s, the robot turns 26° = clear of the wall
```

---

## 🟡 MEDIUM: Front safety zone too narrow

### Problem:
```python
front_half_deg = 10.0  # ±10° ahead

Small robots and LIDARs can have blind spots
10° is ≈ 8cm on each side at 50cm = an obstacle may be hidden
```

### Fix:
```python
front_half_deg = 15.0  # ±15° = better coverage
```

---

## 📋 CHECKLIST OF THE CURRENT CONFIGURATION

### ✅ SLAM Toolbox params (CORRECT):
```yaml
scan_queue_size: 1              # ✓ Short queue
throttle_scans: 1               # ✓ Processes every scan
minimum_travel_distance: 0.1    # ✓ OK
minimum_travel_heading: 0.1     # ⚠️ To be raised to 0.15
use_scan_matching: true         # ✓ Mandatory
```

### ✅ Scan Restamper (CORRECT):
```python
# Fixes the SLAM/LIDAR timestamp sync ✓ WORKING
```

### ✅ Motor Odom Node (OK):
```
linear_vel_scale: 0.8
angular_vel_scale: 0.9
# Without encoders drift is unavoidable - but SLAM corrects it ✓
```

### ✅ Simple EKF (WORKING):
```
Fuse motor_odom + IMU gyro + SLAM pose
# Correct, not the problem ✓
```

### ❌ Wall-Follow params (CRITICAL):
```python
# ALL the parameters above must be changed!
```

---

## 🎯 FIXED VALUES (TO COPY):

```python
# ===== SAFETY DISTANCES (FIXED) =====
d_stop = 0.35   # +40% margin (from 0.25)
d_slow = 0.80   # +33% more progressive (from 0.60)

# ===== SPEED LIMITS (FIXED) =====
v_max = 0.50    # Slightly slower (from 0.60)
v_min = 0.10    # Slightly slower (from 0.15)
w_max = 0.50    # CRITICAL: -80% (from 2.5!)
w_emergency = 1.0  # For emergencies only

# ===== PID TUNING (FIXED) =====
kp = 0.8        # Less aggressive (from 2.0)
kd = 0.6        # Better derivative (from 0.4)

# ===== LIDAR PARAMS (FIXED) =====
front_half_deg = 15.0        # +50% coverage (from 10.0)
fallback_half_deg = 25.0     # +25% (from 20.0)

# ===== SAFETY TIMING (FIXED) =====
emergency_hold_time = 0.8    # +130% (from 0.35)
slam_settle_time = 0.5       # Minimum pause between moves
```

---

## 🧪 TEST PROGRESSION:

1. **Static test**: stop the robot in front of a wall, check d_stop
2. **Linear test**: drive slowly straight ahead, check the mapping
3. **Slow rotation test**: turn @ 0.5 rad/s, check that SLAM keeps up
4. **Wall-follow test**: go round a wall at REDUCED speed
5. **Stress test**: sudden obstacle = check the emergency behaviour

---

## 📍 FILES TO MODIFY:

1. **naif_autonome.py** → Lines 82-95 (params)
2. **algo_naif_v2.py** → Lines 82-97 (params + emergency)
3. **config/slam_toolbox_params.yaml** → Line 18 (minimum_travel_heading)
