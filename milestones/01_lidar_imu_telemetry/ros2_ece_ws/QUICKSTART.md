# 🚀 QUICK START - LIDAR 360° Visualisation

## ⏱️ Reading time: 2 minutes

---

## 🎯 What is in place

✅ **ESP32 circular buffer** (720 points)  
✅ **360° LaserScan publishing**  
✅ **ROS2 listener with statistics**  
✅ **Tuned RViz configuration**  
✅ **Full guide included**  

---

## 📋 3 Steps to Visualise

### 1️⃣ Start the agent (Terminal 1)
```bash
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

### 2️⃣ Upload to the ESP32 (Terminal 2 or IDE)
Open the PlatformIO project and click **Upload**:
```
milestones/01_lidar_imu_telemetry/firmware
```

### 3️⃣ Start the listener + RViz (Terminal 3)
```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source install/setup.bash
ros2 launch cpp_pubsub agent_launch.py
```

**RViz opens automatically → the 360 points show up in RED.** 🎉

---

## 📊 What you will see

```
Terminal:
[INFO] LIDAR Data: 145/360 points valid | Min: 0.25m | Max: 5.67m | Avg: 3.45m | Angle range: 180°

RViz:
┌─────────────────────────────────┐
│  Grey XY grid (reference)       │
│                                 │
│     ●●●●●●●●●●●●●●●●●●●       │
│    ●  RED LIDAR points   ●      │
│     ●●●●●●●●●●●●●●●●●●●       │
│                                 │
│     (3D view, zoom with scroll) │
└─────────────────────────────────┘
```

---

## 🎮 RViz Controls

| Action | Command |
|--------|---------|
| **Zoom** | Mouse scroll |
| **Rotate the view** | Right-click + drag |
| **Pan** | Right-click + Shift + drag |
| **Reset** | Home key |

---

## 🔴 Red points = correctly set up ✓

If the points are **red** → the configuration is right.

If the points have another colour → see the RViz guide.

---

## 📁 Documentation Files

1. **RESUME_MODIFICATIONS.md** (📊 Technical overview)
   - What changed
   - Before/after comparison
   - Technical details

2. **GUIDE_LIDAR_360_COMPLET.md** (📖 Full guide)
   - Complete procedure
   - Detailed configuration
   - Advanced troubleshooting

3. **GUIDE_RVIZ_CONFIGURATION.md** (🎨 RViz only)
   - Manual adjustments
   - Use cases
   - RViz troubleshooting

4. **deploy_lidar.sh** (🚀 Automation script)
   ```bash
   milestones/01_lidar_imu_telemetry/ros2_ece_ws/deploy_lidar.sh
   ```

---

## ✅ Quick Check

Before starting, check:

```bash
# 1. Circular buffer OK?
grep "LIDAR_BUFFER_SIZE 720" \
  milestones/01_lidar_imu_telemetry/firmware/src/main.cpp
# Should print: #define LIDAR_BUFFER_SIZE 720

# 2. RViz config OK?
grep "LaserScan (Tous les 360 points)" \
  milestones/01_lidar_imu_telemetry/ros2_ece_ws/src/cpp_pubsub/launch/lidar.rviz
# Should print: - LaserScan (Tous les 360 points)

# 3. Listener OK?
grep "lidar_callback" \
  milestones/01_lidar_imu_telemetry/ros2_ece_ws/src/cpp_pubsub/src/publisher_member_function.cpp
# Should print: void lidar_callback
```

---

## 🆘 It does not work?

### The points do not show up
```bash
# Check that everything is built:
milestones/01_lidar_imu_telemetry/ros2_ece_ws/deploy_lidar.sh
# Should print: ✅ Système LIDAR 360° prêt au lancement!
```

### RViz shows an error
```bash
# Wait 5 seconds after launch
# RViz configures itself automatically
```

### Terminal 3 prints nothing
```bash
# Check that Terminal 1 (agent) is running:
docker ps | grep micro-ros
# Should list the running container
```

See the "Troubleshooting" section of **GUIDE_LIDAR_360_COMPLET.md** for more.

---

## 📈 Data Flow

```
ESP32 LIDAR (LD06)
        ↓
  [720-pt buffer]
        ↓
  micro_ros_agent
        ↓
  [ROS2 Network]
        ↓
  listener node
        ↓
  [Terminal Output]
        ↓
  RViz Visualization (360°, RED)
```

---

## 💡 Key Points

🎯 **Buffer** = 720 points (60 frames × 12 points)  
📡 **Publishing** = 360-point LaserScan  
🎨 **Colour** = red  
📊 **Display** = real-time statistics  
🎮 **Control** = RViz mouse + keyboard  

---

## 🎓 After the Visualisation

Once it works:

1. **Understand the buffer** → see RESUME_MODIFICATIONS.md
2. **Adjust RViz** → see GUIDE_RVIZ_CONFIGURATION.md
3. **Advanced** → see the "Next steps" section of GUIDE_LIDAR_360_COMPLET.md

---

## ✨ Final Result

```
✅ 360° LIDAR system OPERATIONAL
✅ Every point visible in real time
✅ 3D visualisation in RViz
✅ Raw data kept for ROS2 processing
✅ Full documentation provided
```

---

## 🚀 Summary of the commands

```bash
# Terminal 1
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888

# Terminal 2
# Upload through PlatformIO (Upload button)

# Terminal 3
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source install/setup.bash
ros2 launch cpp_pubsub agent_launch.py
```
