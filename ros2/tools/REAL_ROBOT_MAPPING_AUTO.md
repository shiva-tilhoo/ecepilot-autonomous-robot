# 🤖 REAL ROBOT AUTONOMOUS MAPPING - Full Architecture

## Overview

Complete **3-phase autonomous mapping** system for the real robot on its mat:

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: AUTONOMOUS                                         │
│ - The robot follows the walls (wall_centering_node)        │
│ - Records trajectory + pose (loop_closure_detector)        │
│ - Builds the SLAM Toolbox map                               │
│                                                             │
│ ↓ Detects the return to the start (distance < 0.20m)      │
│                                                             │
│ Phase 2: PLANNING                                           │
│ - A* computes a direct path from current → start          │
│ - Optimised with shortcuts + smoothing                     │
│ - Trajectory available for following                       │
│                                                             │
│ ↓ Path received and validated                             │
│                                                             │
│ Phase 3: RETURNING                                         │
│ - The robot follows the A* path (PID heading control)     │
│ - Reaches the start point accurately                      │
│ - Mission COMPLETED                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 The 4 Key Files

### 1. `loop_closure_detector.py` 🔍
**Detects the loop + records the trajectory**

- **Listens to:** robot pose through `/tf` (map → base_link)
- **Publishes:**
  - `/loop_closure/return_detected` (Bool) - Detection signal
  - `/loop_closure/distance_to_start` (Float32) - Distance to the start
  - `/loop_closure/trajectory_point` (PoseStamped) - Sampled points
- **Logic:**
  1. Waits until the robot moves away (> LEAVE_START_DISTANCE = 0.60m)
  2. Enables trajectory recording
  3. Samples every LAP_SAMPLE_DISTANCE = 0.08m
  4. Detects distance < RETURN_DETECTION_DISTANCE = 0.20m
  5. Signals the completed loop after EXTRA_DISTANCE_AFTER_RETURN = 2.0m

**Outputs:** `~/trajectories/auto_mapping/trajectory_*.json` + `.npy`

### 2. `trajectory_saver.py` 💾
**Handles trajectory saving**

- **Listens to:** points from `/loop_closure/trajectory_point`
- **Output formats:**
  - JSON (human readable)
  - NumPy (.npy - fast access)
  - CSV (compatibility)
  - Stats (.json - min/max/length)
- **Methods:**
  - `save_all_formats()` saves every format
  - `optimize_trajectory()` smooths noisy points
  - Automatic save on Ctrl+C

### 3. `return_path_generator.py` 🗺️
**A* planning on the real SLAM map**

- **Listens to:**
  - `/map` (OccupancyGrid from SLAM)
  - `/loop_closure/return_detected` (signal)
  - `/loop_closure/trajectory_point` (start point)
- **Publishes:**
  - `/return_path` (Path - points of the path)
  - `/return_waypoints` (Float32MultiArray)
- **Algorithm:**
  - Converts the SLAM map into a grid
  - A* pathfinding (Euclidean heuristic)
  - Optimisation: shortcuts + obstacle inflation
  - Moving-average smoothing
  - World ↔ grid conversion

**Tuning parameters:**
```
ASTAR_CELL_SIZE_M = 0.08              # Grid resolution
ASTAR_INFLATION_CELLS = 4             # Obstacle safety margin
ASTAR_OBSTACLE_THRESHOLD = 50         # Occupied threshold (0-100)
ASTAR_SHORTCUT_MAX_SKIP = 20          # Max shortcut jump
ASTAR_ALLOW_DIAGONAL = True           # 8-direction moves
```

### 4. `real_robot_mapping_auto.py` 🎬
**Orchestrator + return path following**

- **Runs the state machine:**
  - `AUTONOME` - wall_centering_node active
  - `RETURN_PLANNED` - Waiting for the A* path
  - `RETURNING` - PID path following
  - `COMPLETED` - Goal reached
- **PID control for the return:**
  ```
  heading_error = desired_heading - robot_theta
  angular_cmd = KP * error + KD * (error - error_prev)
  ```
- **Loads every node:** starts the 4 of them in the right order
- **Signals:** publishes `/mapping_completed` (Bool) when done

**Return PID parameters:**
```python
return_kp = 1.8              # Proportional
return_kd = 0.25             # Derivative
return_lookahead_m = 0.3      # Look-ahead distance
return_goal_tolerance_m = 0.15  # Goal radius
return_max_speed = 0.5        # Linear speed
```

---

## 🚀 Getting Started

### Requirements

1. **SLAM Toolbox running:**
   ```bash
   ./start_robot_mapping_auto.sh
   ```

2. **ESP32 LiDAR active** (`/scan_raw` topic)

3. **TF publishing active** (`/tf` map→base_link from SLAM)

### Full Launch

**Option 1: Shell script (recommended)**
```bash
chmod +x real_robot_mapping_auto.sh
./real_robot_mapping_auto.sh
```

**Option 2: Individual nodes**
```bash
# Terminal 1
python3 wall_centering_node.py

# Terminal 2
python3 loop_closure_detector.py

# Terminal 3
python3 trajectory_saver.py

# Terminal 4
python3 return_path_generator.py

# Terminal 5 (orchestrator)
python3 real_robot_mapping_auto.py
```

---

## 📊 Monitoring

### Available ROS topics

```bash
# Mission state
ros2 topic echo /loop_closure/return_detected        # Loop signal
ros2 topic echo /loop_closure/distance_to_start      # Distance to start (m)
ros2 topic echo /mapping_completed                   # End signal

# Computed path
ros2 topic echo /return_path                         # ROS Path

# Recorded trajectory
ros2 topic echo /loop_closure/trajectory_point       # Points (stream)
```

### Logs

```bash
# Real-time logs (shell script)
tail -f /tmp/mapping_auto_logs/*.log

# Individual logs
tail -f /tmp/mapping_auto_logs/wall_centering.log
tail -f /tmp/mapping_auto_logs/loop_closure.log
tail -f /tmp/mapping_auto_logs/return_path.log
tail -f /tmp/mapping_auto_logs/trajectory_saver.log
```

### Saved files

```
~/trajectories/auto_mapping/
├── trajectory_20260320_092105.json    # Readable format
├── trajectory_20260320_092105.npy     # NumPy format
├── trajectory_20260320_092105.csv     # CSV format
└── trajectory_20260320_092105_stats.json  # Statistics

~/mapping_logs/
└── mission_1711000865.json           # Mission logs
```

---

## ⚙️ Fine Tuning

### Fast robot → Increase the reaction time
```python
# loop_closure_detector.py
RETURN_DETECTION_DISTANCE = 0.30        # Larger tolerance
LAP_SAMPLE_DISTANCE = 0.15              # Fewer points

# real_robot_mapping_auto.py
return_kp = 2.5                         # More decisive
return_kd = 0.4                         # Less overshoot
```

### Close obstacles → Increase the safety distance
```python
# return_path_generator.py
ASTAR_INFLATION_CELLS = 6               # Wider
ASTAR_SHORTCUT_CLEARANCE_M = 0.50       # Stricter
```

### Poor-quality map → Simplify the path
```python
# return_path_generator.py
ASTAR_SHORTCUT_MAX_SKIP = 40            # More shortcuts
ASTAR_MIN_PATH_KEEP_RATIO = 0.30        # Accepts a shorter path
```

---

## 🔧 Troubleshooting

### ❌ "Phase 1 starts but the robot does not move"
```bash
# Check wall_centering_node
ros2 topic echo /cmd_vel                    # Are commands sent?
ros2 topic echo /scan                       # Is the LiDAR received?
ros2 service call /freeze_scan std_srvs/...  # Test the service
```

### ❌ "The loop is never detected"
```
- Increase the lookahead: LEAVE_START_DISTANCE = 1.0m
- Loosen the tolerance: RETURN_DETECTION_DISTANCE = 0.30m
- Check the TF: ros2 run tf2_tools view_frames
```

### ❌ "A* fails - no path"
```
- Increase the inflation: ASTAR_INFLATION_CELLS = 8
- Lower the obstacle threshold: ASTAR_OBSTACLE_THRESHOLD = 60
- Check /map: ros2 topic echo /map | head -20
```

### ❌ "The return drifts away from the path"
```
- Increase KP: return_kp = 2.5
- Lower the speed: return_max_speed = 0.3
- Reduce the lookahead: return_lookahead_m = 0.15
```

---

## 📈 Future Improvements

- [ ] Nav2 integration instead of the simple PID
- [ ] Multi-loop support (several circuits)
- [ ] Loop closure graph optimisation (pose graph)
- [ ] Dynamic obstacle avoidance during the return
- [ ] Global trajectory correction through ICP
- [ ] Automatic parameter tuning (AutoML)

---

## 📝 Detailed Architecture

### Data flow

```
[wall_centering_node]
        ↓ (autonomy + TF)
   [loop_closure_detector]
        ├→ [trajectory_saver]
        └→ Loop signal ↓
   [return_path_generator]
        ├→ Listens to the SLAM /map
        ├→ A* planning
        └→ Publishes /return_path
                ↓
[real_robot_mapping_auto]
        ├→ Receives the path
        ├→ PID following
        └→ Publishes /cmd_vel_return
```

### State Transitions

```
┌──────────┐
│ AUTONOME │ (wall_centering active)
│          │
└─────┬────┘
      │ distance_to_start < 0.20m
      │ + distance_traveled > 3.0m
      ↓
┌──────────────────┐
│ RETURN_PLANNED   │ (Waiting for the A* path)
│                  │
└─────┬────────────┘
      │ len(return_path) > 0
      ↓
┌──────────┐
│ RETURNING│ (Path following + PID)
│          │
└─────┬────┘
      │ distance_to_goal < 0.15m
      ↓
┌──────────┐
│COMPLETED │ (Mission done!)
│          │
└──────────┘
```

---

## 📚 References

- **SLAM Toolbox Config:** `config/slam_toolbox_minimal.yaml`
- **Wall Centering Control:** `wall_centering_node.py` (line ~820)
- **Scan Restamper:** `scan_restamper_simple.py` (throttle 1/4)
- **Simulation reference:** `simu_lidar_auto.py` (1273 lines)

---

**Version:** 1.0 - Robot ECE Project  
**Date:** March 2026  
**Status:** ✅ Production Ready
