# 🚀 Quick Start - Autonomous Navigation with SLAM

**Start the mapping and autonomous navigation system with SLAM Toolbox, micro-ROS and ROS2 Humble.**

## ⚡ 5 Minutes Setup

### 1️⃣ **Check the Hardware**

```
ESP32                   LIDAR LD06            Motor Driver
─────────────────────────────────────────────────────────
GPIO16 (UART RX2) ←─── TX (LaserScan)
GPIO25 (PWM) ─────────→ M_SCTR (Motor control)
GPIO32, GPIO33 ───────→ Motor encoder inputs
GPIO23, GPIO19 ───────→ Motor PWM outputs (L298N)
GND ──────────────────→ GND
5V ───────────────────→ VCC

IMU MPU6050:
GPIO21 (SDA) ──────── SDA
GPIO22 (SCL) ──────── SCL
GND ──────────────── GND
3.3V ────────────── VCC
```

### 2️⃣ **Build and Upload the ESP32 Firmware**

**Option A: PlatformIO CLI**
```bash
cd milestones/03_custom_slam_ekf_fusion
pio run -e esp32dev -t upload
pio device monitor -b 115200  # Watch the logs
```

**Option B: VS Code**
- Right-click on `src/main.cpp`
- "PlatformIO: Upload"

### 3️⃣ **Start the micro-ROS Agent**

```bash
# Terminal 1 - Docker agent (port 8888)
docker run -it --rm -v /dev:/dev --privileged \
  microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 \
  --ip 0.0.0.0 --port 8888
```

✅ You should see: `[INFO] [UDPv4AgentLinux]: Client connected from IP 172.20.10.x`

### 4️⃣ **Start the ROS2 Stack**

```bash
# Terminal 2 - Start every node
cd milestones/03_custom_slam_ekf_fusion
chmod +x start_stack.sh
./start_stack.sh
```

**What gets started:**
1. ✅ Micro-ROS Agent (checks whether it is connected)
2. ✅ RViz2 (visualisation)
3. ✅ IMU FIR Filter (smooths the LIDAR vibrations)
4. ✅ Motor Odometry Node (estimates the robot position)
5. ✅ Scan Restamper (fixes the timestamps)
6. ✅ SLAM Toolbox (builds the map)
7. ✅ Simple EKF (fuses odom + IMU)

### 5️⃣ **Check the Topics**

```bash
# Terminal 3 - List the active topics
ros2 topic list

# Should display:
/odom                   # Motor odometry
/odom_filtered          # Fused odometry (odom + IMU)
/scan                   # LIDAR scans (re-stamped)
/scan_raw              # Raw scans (before re-stamping)
/imu/data              # Raw IMU
/imu/data_filtered     # Smoothed IMU
/map                   # SLAM map (occupancy grid)
/tf                    # Transforms
/cmd_vel               # Motion commands
```

### 6️⃣ **Drive the Robot**

```bash
# Terminal 4 - Keyboard (WASD)
cd milestones/03_custom_slam_ekf_fusion
python3 teleop_keyboard.py
```

**Keys:**
- **W** = Forward (0.3 m/s)
- **A** = Turn left (1.5 rad/s)
- **S** = Backward (-0.3 m/s)
- **D** = Turn right (-1.5 rad/s)
- **Space** = Stop
- **Q** = Quit

### 7️⃣ **View the Map in RViz**

1. **Open RViz** (started automatically by start_stack.sh)
2. **Fixed Frame** → `map`
3. **Add Display** → add:
   - ✅ **Map** (topic: `/map`)
   - ✅ **LaserScan** (topic: `/scan`)
   - ✅ **Odometry** (topic: `/odom_filtered`)
   - ✅ **TF** (for the frames)

**You should see:**
- 🔵 Blue robot in the centre
- 🟩 Grey grid (occupied map)
- 🔴 Red points (LIDAR scans)
- 🟦 Arrow (robot heading)

---

## 🧪 Automated Test

```bash
# Send test commands (forward → rotation → stop)
python3 test_movement.py
```

Check that:
- ✅ The position changes: `ros2 topic echo /odom`
- ✅ Scans accumulate: RViz shows more points
- ✅ The map updates: `/map` changes

---

## 🔧 Troubleshooting

### ❌ The `/map` topic does not exist
```bash
# Check that SLAM is running
ros2 topic list | grep map
ros2 topic hz /map  # Should show 1Hz
```

**Solution:** check that `/scan` is published (the restamper must be running)

### ❌ Scans do not accumulate in RViz
```bash
# Check the scan timestamps
ros2 topic echo /scan --max-count=1 | grep stamp
```

**Solution:** the timestamp must be the current time, not 8000+ s

### ❌ The robot does not move
```bash
# Run test_movement.py and check /odom
ros2 topic echo /odom --max-count=1
```

**Solution:** the motor odometry needs `/cmd_vel` to move

### ❌ No micro-ROS connection
```bash
# Check the ESP32
pio device monitor -b 115200

# Restart the agent
pkill -f micro_ros_agent
docker run -it --rm ... ros2 run micro_ros_agent ...
```

---

## 📊 Topics and Frames Hierarchy

```
map (frame of the SLAM map)
├── odom (odometry frame)
│   └── base_link (robot frame)
│       └── laser_link (LIDAR)
└── imu_link (IMU)

Key topics:
/scan          → LaserScan (LIDAR, 10Hz)
/odom          → Odometry (motor, 50Hz)
/odom_filtered → Odometry (fused, 50Hz)
/imu/data      → Imu (100Hz raw)
/imu/data_filtered → Imu (100Hz smoothed)
/map           → OccupancyGrid (SLAM, 1Hz)
/tf            → Dynamic transforms
/cmd_vel       → Twist (motor commands)
```

---

## 📝 Start-up Checklist

- [ ] ESP32 built and flashed
- [ ] LIDAR + IMU wired
- [ ] Docker micro-ROS agent running (port 8888)
- [ ] `./start_stack.sh` started without errors
- [ ] RViz open with the right displays
- [ ] `ros2 topic list` shows `/scan`, `/odom`, `/map`
- [ ] Keyboard teleop works (W/A/S/D)
- [ ] The robot moves in RViz
- [ ] The map updates around the robot

**If everything is ✅: the system works! 🎉**

---

## 📚 Next Steps

1. **See [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)** - Complete system architecture
2. **See [SLAM_IMPLEMENTATION.md](../../docs/SLAM_IMPLEMENTATION.md)** - Detailed SLAM algorithm
3. **See [PERFORMANCE.md](../../docs/PERFORMANCE.md)** - Comparison before/after the optimisations
4. **Configure Nav2** - For autonomous (not manual) navigation
5. **Add loop closure** - For large maps without drift

---

## ⚠️ Important Notes

### Timestamps
- ESP32 boot time (sec: ~8000) vs ROS2 wall clock (sec: ~1770000000)
- **Solution:** `scan_restamper.py` re-stamps automatically
- If `/map` stays empty → check that the restamper is running

### Odometry
- Motor odometry **depends on `/cmd_vel`** to compute the position
- No command = static position (correct)
- The EKF fusion corrects the drift with SLAM

### SLAM Toolbox
- `mapping` mode: accumulates every scan
- `0.025m` resolution = 2.5cm/pixel (very accurate, 5x5m area)
- Ceres solver with SPARSE_NORMAL_CHOLESKY (fast, low CPU)

---

**Version:** 1.0 (February 2026) | **Status:** ✅ Stable & Tested
