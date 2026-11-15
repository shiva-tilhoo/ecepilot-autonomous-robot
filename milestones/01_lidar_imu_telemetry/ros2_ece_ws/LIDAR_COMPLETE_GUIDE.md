# 🚀 Complete Guide - ROS2 + LIDAR + ESP32 + micro_ros

## 📋 Full Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   COMPLETE LIDAR SYSTEM                     │
├──────────────────────┬──────────────────┬──────────────────┤
│   ESP32 + LD06       │   ROS2 Humble    │   Visualisation  │
│                      │                  │                  │
│  ┌────────────────┐  │  ┌────────────┐  │  ┌────────────┐  │
│  │ LIDAR LD06     │  │  │ Publisher  │  │  │   RViz2    │  │
│  │ (230400 baud)  ├──┼─►│ talker     ├──┼─►│ LaserScan  │  │
│  │                │  │  │            │  │  │ Viewer     │  │
│  └────────────────┘  │  └────────────┘  │  └────────────┘  │
│         │            │         │        │         │        │
│  ┌────────────────┐  │  ┌────────────┐  │         │        │
│  │ micro_ros      │  │  │ Subscriber │  │         │        │
│  │ WiFi Agent     ├──┼─►│ listener   ├──┼─► Console Log   │
│  │ UDP:8888       │  │  │ (Analysis) │  │                 │
│  └────────────────┘  │  └────────────┘  │         │        │
└──────────────────────┴──────────────────┴─────────────────┘
         │                   │                      │
         └───────────────────┴──────────────────────┘
              ROS2 Topics: /scan, /data
```

## ⚡ 5 Minutes Quick Start

### Step 1: Build

```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
colcon build --packages-select cpp_pubsub
source install/setup.bash
```

### Step 2: Start the nodes

**Terminal 1 - Publisher:**
```bash
ros2 run cpp_pubsub talker
```

**Terminal 2 - Subscriber:**
```bash
ros2 run cpp_pubsub listener
```

### Step 3: Look at the data

```bash
# Terminal 3 - Console output of the subscriber
ros2 topic echo /scan --max-count=3
```

## 📊 Architecture in Detail

### Components

#### 1. **talker** (Publisher)
- **Executable:** `cpp_pubsub/talker`
- **Published topics:** `/scan` (LaserScan), `/data` (Int32)
- **Rate:** 10 Hz
- **Generated data:** simulated LIDAR scans for testing

**File:** `src/publisher_member_function.cpp`

```cpp
// Create the publishers
lidar_publisher_ = create_publisher<LaserScan>("/scan", 10);
counter_publisher_ = create_publisher<Int32>("/data", 10);

// Timer callback every 100ms
timer_ = create_wall_timer(100ms, timer_callback);
```

#### 2. **listener** (Subscriber)
- **Executable:** `cpp_pubsub/listener`
- **Subscribed topics:** `/scan`, `/data`
- **Processing:** analysis + display
- **Output:** detailed console logs

**File:** `src/subscriber_member_function.cpp`

**Analysis performed:**
- ✓ Closest obstacle detection
- ✓ Obstacle-ahead alert (±15°, <1m)
- ✓ Distance statistics
- ✓ Debug of the first points

#### 3. **ROS2 configuration**
- **Package:** `cpp_pubsub`
- **Dependencies:** rclcpp, sensor_msgs, std_msgs
- **Build system:** ament_cmake

## 🔌 ROS2 Topics

### `/scan` - sensor_msgs/LaserScan

**Format:**
```yaml
header:
  stamp:
    sec: 1705715400
    nanosec: 500000000
  frame_id: "lidar_link"

angle_min: 0.0           # radians
angle_max: 6.28318       # 2π radians (360°)
angle_increment: 0.01745 # ~1 degree

time_increment: 0.0
scan_time: 0.1           # 100ms
range_min: 0.06          # 60mm
range_max: 12.0          # 12m

ranges: [5.23, 5.15, 4.89, ...]  # Distances in metres
intensities: [100, 120, 95, ...]  # Signal strength
```

### `/data` - std_msgs/Int32

**Format:**
```yaml
data: 42  # Simple counter
```

## 🚀 Launch Options

### 1. Simple (individual executables)

```bash
# Terminal 1
ros2 run cpp_pubsub talker

# Terminal 2
ros2 run cpp_pubsub listener
```

### 2. Launch File

```bash
ros2 launch cpp_pubsub lidar_launch.py
```

**File:** `launch/lidar_launch.py`
- Starts talker + listener
- Same terminal

### 3. Full (with RViz)

```bash
ros2 launch cpp_pubsub lidar_complete_launch.py
```

**File:** `launch/lidar_complete_launch.py`
- Starts talker + listener + rviz2
- Each node in its own terminal

### 4. With the micro_ros Agent (ESP32)

```bash
# Terminal 1 - Agent
docker run -it --rm \
  -v /dev:/dev --privileged \
  microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --ip 0.0.0.0 --port 8888

# Terminal 2 - ROS2 nodes
ros2 launch cpp_pubsub agent_launch.py

# Terminal 3 - Monitor
ros2 topic echo /scan
```

## 📈 Data Analysis (Subscriber)

The subscriber automatically prints:

```
════════════════════════════════════════════
🔍 SCAN LIDAR #1 reçu
Frame ID: lidar_link
Nombre de points: 360
Angle Min/Max: 0.00 / 6.28 rad (0.0° / 360.0°)
Angle Increment: 0.0175 rad (1.00°)
Range Min/Max: 0.06 / 12.00 m
════════════════════════════════════════════

⚠️  Obstacle le plus proche: 0.52 m @ indice 45 (angle: 45.0°)
📈 Statistiques - Points valides: 360 / 360, Distance moyenne: 5.32 m
```

**Key information:**

1. **Global obstacle:** closest point
2. **Danger ahead:** if <1m within the ±15° cone
3. **Statistics:** valid points + average
4. **Debug:** first 5 points (with ROS_LOG_LEVEL=DEBUG)

## 🎨 RViz Visualisation

### Starting RViz

```bash
# Simple
rviz2

# With the provided config
rviz2 -d milestones/01_lidar_imu_telemetry/ros2_ece_ws/src/cpp_pubsub/launch/lidar.rviz
```

### Configuration

1. **Fixed Frame:** `lidar_link`
2. **Display:** LaserScan
3. **Topic:** `/scan`
4. **Color:** gradient (intensity)

## 🔗 Integration with the ESP32

### Full Architecture

```
ESP32 (micro_ros client)
  │
  ├─ UART (GPIO16) ← LIDAR LD06
  │
  └─ WiFi
      │
      └─ UDP8888 (micro_ros agent)
          │
          └─ ROS2 Network
              │
              ├─ /scan ──► talker (Publisher)
              │             │
              │             └─► listener (Subscriber)
              │                   │
              │                   └─► Console + RViz
              │
              └─ /data ──► talker (Int32)
```

### Deployment Steps

#### 1. Configure the ESP32
```cpp
// In firmware/src/main.cpp

#define LIDAR_ENABLED 1
#define LIDAR_RX 16
#define LIDAR_BAUD 230400

// Publish on /scan (LaserScan)
rcl_publisher_t pub_lidar;
// Publish on /data (Int32)
rcl_publisher_t pub_int;
```

#### 2. Upload to the ESP32
```bash
cd milestones/01_lidar_imu_telemetry/firmware
pio run -e esp32dev -t upload
```

#### 3. Start the agent
```bash
docker run -it --rm \
  -v /dev:/dev --privileged \
  microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --ip 0.0.0.0 --port 8888
```

#### 4. Check the connection
```bash
# List every topic
ros2 topic list

# Must list:
# /scan
# /data
```

#### 5. Start the nodes
```bash
ros2 launch cpp_pubsub agent_launch.py
```

## 🛠️ Helper Script

```bash
# Run the script
milestones/01_lidar_imu_telemetry/ros2_ece_ws/run_lidar.sh [OPTION]

# Options
publisher       # Start talker only
subscriber      # Start listener only
launch          # Start with the launch file
launch-complete # Full start (RViz)
agent           # Start to receive from the ESP32
monitor         # Watch the topics
build           # Rebuild
clean           # Clean the build
```

## 📊 Monitoring and Debug

### Live Topics

```bash
# List every topic
ros2 topic list

# Detailed information
ros2 topic info /scan

# Rate
ros2 topic hz /scan

# Bandwidth used
ros2 topic bw /scan
```

### Detailed Logs

```bash
# DEBUG level
ROS_LOG_LEVEL=DEBUG ros2 run cpp_pubsub listener

# Available log levels
# DEBUG, INFO, WARN, ERROR, FATAL
```

### Recording the data

```bash
# Record a rosbag
ros2 bag record /scan /data

# Replay
ros2 bag play rosbag2_*
```

## 📁 Full Structure

```
ros2_ece_ws/
├── src/
│   └── cpp_pubsub/
│       ├── src/
│       │   ├── publisher_member_function.cpp     ← talker
│       │   ├── subscriber_member_function.cpp    ← listener
│       │   └── ultrasonic_processor.cpp
│       │
│       ├── launch/
│       │   ├── lidar_launch.py                   ← Simple
│       │   ├── lidar_complete_launch.py          ← Full
│       │   ├── agent_launch.py                   ← With the agent
│       │   └── lidar.rviz                        ← RViz config
│       │
│       ├── CMakeLists.txt                        ← Build config
│       ├── package.xml                           ← Dependencies
│       └── README.md                             ← Documentation
│
├── run_lidar.sh                                   ← Helper script
└── install/
    └── setup.bash                                 ← Source this!
```

## 🎓 Concepts Used

1. **ROS2 nodes:** talker (pub) + listener (sub)
2. **Publishers/Subscribers:** asynchronous communication
3. **Topics:** /scan (LaserScan), /data (Int32)
4. **Messages:** sensor_msgs/LaserScan standard format
5. **Launch files:** automatic orchestration
6. **RViz:** 3D visualisation
7. **micro_ros:** ESP32 ↔ ROS2 communication

## 🔄 Complete Data Flow

```
1. ESP32 (or simulated talker)
   │
   ├─ Generates LIDAR data
   └─ Publishes on /scan + /data
   
2. ROS2 Network
   │
   ├─ Receives the messages
   └─ Routes them to the subscribers
   
3. Subscriber (listener)
   │
   ├─ Receives /scan
   ├─ Receives /data
   ├─ Analyses the data
   └─ Prints the results
   
4. Visualisation (RViz)
   │
   ├─ Displays the LIDAR points
   ├─ Grid + obstacles
   └─ Real time
```

## 🚀 Next Steps

1. **Recording:** `ros2 bag record /scan`
2. **Processing:** create a custom processing node
3. **Avoidance:** implement the obstacle logic
4. **Navigation:** integrate with nav2_core
5. **SLAM:** add autonomous mapping

## 📞 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Topics not visible | `source install/setup.bash` |
| Empty RViz | Fixed Frame = "lidar_link" |
| Build fails | `rosdep install --from-paths src` |
| No ESP32 connection | Check the agent + WiFi |
| Missing data | Check the /scan + /data topics |

---

**📌 Important file:** [README.md](./src/cpp_pubsub/README.md)  
**📌 Helper script:** `milestones/01_lidar_imu_telemetry/ros2_ece_ws/run_lidar.sh`  
**📌 RViz configuration:** `launch/lidar.rviz`

**Date:** 2026-01-19  
**Version:** 1.0.0
