# 🗺️ SLAM Toolbox Setup - Full Explanation

**Date:** February 2026  
**Based on:** the SLAM lecture handout of the course

---

## 📚 What the course says

The handout **clearly** recommends:
1. ❌ Do NOT reinvent the wheel with a custom SLAM
2. ✅ Use **SLAM Toolbox** - a ready-to-use ROS2 library
3. ✅ Use **Nav2** - a complete framework for autonomous navigation

---

## 🎯 What is SLAM Toolbox for?

### **SLAM = Simultaneous Localization And Mapping**

**In plain words:**
- **Mapping** = building a map of the environment in real time
- **Localization** = knowing where the robot is in the map
- **Simultaneous** = doing both at the same time

### **In practice, SLAM Toolbox:**

```
LIDAR scans (sensor)
    ↓
SLAM Toolbox
    ├─→ Accumulates the scans in a STATIC map (/map frame)
    ├─→ Estimates the robot pose (x, y, theta)
    ├─→ Detects closed loops (loop closure)
    └─→ Keeps improving the accuracy
    ↓
/map (STATIC)
/slam_toolbox/pose (where the robot is)
```

---

## 🛠️ Configuration for the robot

File: `config/slam_toolbox_params.yaml`

### **Key parameters:**

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `scan_topic` | `/scan` | LIDAR topic (where the scans come from) |
| `resolution` | `0.05` | 5cm per cell (very accurate) |
| `minimum_travel_distance` | `0.1m` | Waits for 10cm before adding a scan |
| `minimum_travel_heading` | `0.0998rad` | Waits for 5.7° before adding a scan |
| `map_update_interval` | `0.2s` | Publishes the map 5 times per second |
| `loop_search_distance` | `5.0m` | Looks for loops within 5m |
| `do_loop_closing` | `true` | Detects and closes loops |

### **Why these values?**

**`minimum_travel_distance` = 0.1m**
- ✅ Avoids adding identical scans to the map
- ✅ Saves memory
- ✅ Reduces computation

**`minimum_travel_heading` = 0.0998rad (~5.7°)**
- ✅ Forces the robot to turn before a scan is added
- ✅ Reduces angular redundancy
- ✅ Improves the map quality

**`loop_search_distance` = 5.0m**
- ✅ Detects when the robot comes back to a known place
- ✅ Corrects small odometry errors
- ✅ Makes the map more consistent

---

## 🚀 How does it work in practice?

### **Startup (start_stack.sh):**

```bash
[1/7] Micro-ROS Agent (ESP32)
      └─→ Reads: /odom, /imu, /scan

[2/7] RViz2 (Visualisation)
      └─→ Displays the map and the robot pose

[3/7] IMU FIR Filter (Filter)
      └─→ Removes the LIDAR noise at 20Hz

[4/7] Motor Odometry
      └─→ Computes: robot displacement

[5/7] SLAM Toolbox (SLAM)
      └─→ Fuses: LIDAR + odometry
      └─→ Publishes: /map, /slam_toolbox/pose

[6/7] Kalman Filter Fusion (Fusion)
      └─→ Fuses: Odom + IMU + SLAM
      └─→ Publishes: /odom_filtered (best pose)
```

### **Data flow:**

```
ESP32 (Sensors)
  ├─ /imu/data
  ├─ /scan (raw LIDAR)
  └─ Motor odometry
    ↓
[IMU FIR Filter] → /imu/data_filtered
    ↓
[Motor Odom Node] → /odom (raw odometry)
    ↓
[SLAM Toolbox] 
  Inputs: /scan, /odom
  Outputs:
    ├─ /map (5cm grid, STATIC)
    ├─ /slam_toolbox/pose (estimated pose)
    └─ /tf (map → odom → base_link)
    ↓
[Kalman Fusion]
  Inputs: /odom, /imu/data_filtered, /slam_toolbox/pose
  Output: /odom_filtered (best pose estimate)
    ↓
For Nav2 / autonomous navigation
```

---

## 📊 Important topics

After starting `start_stack.sh`:

```bash
# Inputs (sensors)
/scan                      # Raw LIDAR (10 Hz)
/odom                      # Raw motor odometry
/imu/data                  # Raw IMU

# Filter outputs
/imu/data_filtered         # Filtered IMU (20Hz cutoff)

# SLAM Toolbox outputs
/map                       # Occupancy map (STATIC!)
/slam_toolbox/pose         # Pose estimated by SLAM

# Kalman fusion outputs
/odom_filtered             # Best pose estimate

# Transforms (TF)
map → odom → base_link
```

---

## 🔍 Difference: SLAM Toolbox vs Custom Code

### **SLAM Toolbox (Production):**
```python
✅ Robust, tested in industry
✅ Optimised in C++
✅ Handles loop closure automatically
✅ Detects circular moves
✅ Uses graphs (graph-SLAM)
✅ Little tuning needed
```

### **Custom SLAM (Development):**
```
❌ Prone to bugs
❌ Slow (Python)
❌ No loop closure
❌ The map followed the robot
❌ A lot of manual handling
❌ A lot of tuning needed
```

---

## 🎮 Useful commands

### **Start the full stack:**
```bash
bash start_stack.sh
```

### **Stop cleanly:**
```bash
Ctrl+C
```

### **Check that SLAM Toolbox publishes:**
```bash
ros2 topic echo /slam_toolbox/pose          # Estimated pose
ros2 topic echo /map                        # Map (grid)
ros2 topic hz /slam_toolbox/pose            # Rate
```

### **View in RViz:**
```bash
# /map layer
# /slam_toolbox/pose
# /base_link, /map frames
```

---

## 📈 Next steps (Nav2)

With SLAM Toolbox providing a **STATIC map** and an **estimated pose**, 
**Nav2** can now be used for:

1. **Planning** → computing paths
2. **Control** → following the paths  
3. **Avoidance** → avoiding dynamic obstacles
4. Full **autonomous navigation**

See: `start_nav2_stack.sh` (if available)

---

## 💡 Key points to remember

| Concept | Before (custom) | Now (Toolbox) |
|---------|---|---|
| **Map** | Followed the robot | STATIC (/map frame) |
| **Pose** | Confusing | SLAM Toolbox pose |
| **Loop closing** | None | Automatic |
| **Maintenance** | Hard | Simple (YAML config) |
| **Production** | No | Yes |

---

## 📚 Official resources

- **Course handout:** SLAM lecture of the ECEPILOT project (not included in this repository)
- **SLAM Toolbox Docs:** https://github.com/SteveMacenski/slam_toolbox
- **Nav2 Docs:** https://docs.nav2.org/
- **Tutorials:** YouTube "ROS2 SLAM Toolbox"

---

**Written: 11 February 2026**  
**Configured for:** ECE Pilot - Autonomous Car Project
