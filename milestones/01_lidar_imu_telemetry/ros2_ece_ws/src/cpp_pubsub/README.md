# 📊 ROS2 LIDAR Publisher/Subscriber

## 🎯 Overview

This ROS2 package implements a complete architecture to process LIDAR data:
- **Publisher**: publishes the LIDAR data on `/scan` (sensor_msgs/LaserScan)
- **Subscriber**: receives and displays the data with some analysis
- **Topics**: `/scan` (LaserScan) + `/data` (Int32 counter)

## 📦 Package Structure

```
cpp_pubsub/
├── src/
│   ├── publisher_member_function.cpp   # LIDAR Publisher
│   ├── subscriber_member_function.cpp  # LIDAR Subscriber
│   └── ultrasonic_processor.cpp        # Additional processor
├── launch/
│   ├── lidar_launch.py                 # Simple launch
│   ├── lidar_complete_launch.py        # Full launch (RViz)
│   ├── agent_launch.py                 # Launch with the agent
│   └── lidar.rviz                      # RViz config
├── CMakeLists.txt                      # Build config
└── package.xml                         # Dependencies
```

## 🚀 Installation and Build

### 1. Build the package

```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
colcon build --packages-select cpp_pubsub

# Or with symlinks
colcon build --packages-select cpp_pubsub --symlink-install
```

### 2. Source the environment

```bash
source install/setup.bash
```

## 📡 Running

### Option 1: Start the nodes individually

**Terminal 1 - Publisher (LIDAR):**
```bash
ros2 run cpp_pubsub talker
```

**Terminal 2 - Subscriber (console):**
```bash
ros2 run cpp_pubsub listener
```

**Terminal 3 - Check the topics:**
```bash
ros2 topic list          # List every topic
ros2 topic info /scan    # Information about /scan
ros2 topic hz /scan      # Publishing rate
```

### Option 2: Use a launch file

```bash
# Simple (Publisher + Subscriber)
ros2 launch cpp_pubsub lidar_launch.py

# Full (Publisher + Subscriber + RViz)
ros2 launch cpp_pubsub lidar_complete_launch.py

# With the micro_ros agent
ros2 launch cpp_pubsub agent_launch.py
```

## 🔌 ROS2 Topics

### `/scan` - sensor_msgs/LaserScan
**Published by:** `talker` (Publisher)

LIDAR data with:
- Header (frame_id, timestamp)
- Angles (min, max, increment)
- Ranges (distances in metres)
- Intensities (signal strengths)

**Example:**
```bash
ros2 topic echo /scan --max-count=3
```

### `/data` - std_msgs/Int32
**Published by:** `talker` (Publisher)

Simple counter to test synchronisation

**Example:**
```bash
ros2 topic echo /data
```

## 📊 Displayed Data (Subscriber)

The subscriber automatically prints:

1. **General scan information:**
   - Frame ID
   - Number of points
   - Angle range
   - Distance range

2. **Closest obstacle:**
   - Minimum distance
   - Index and angle

3. **Danger ahead:**
   - If an obstacle is closer than 1m in the ±15° frontal cone

4. **Statistics:**
   - Number of valid points
   - Average distance

5. **Debug info:**
   - First points (at DEBUG level)

## 🎨 RViz Visualisation

### Starting RViz alone

```bash
rviz2
```

### Configuring RViz

1. **Fixed Frame:** change it to `lidar_link`
2. **Add Display:** click "Add" at the bottom left
3. **Select LaserScan:** look for it in the list
4. **Topic:** select `/scan`

### Using the provided config

```bash
rviz2 -d milestones/01_lidar_imu_telemetry/ros2_ece_ws/src/cpp_pubsub/launch/lidar.rviz
```

## 🔗 ESP32 + micro_ros Integration

### Terminal 1 - Start the agent

```bash
docker run -it --rm \
  -v /dev:/dev --privileged \
  microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --ip 0.0.0.0 --port 8888
```

### Terminal 2 - Start the ROS2 nodes

```bash
ros2 launch cpp_pubsub agent_launch.py
```

### Terminal 3 - Check the connection

```bash
# List the connected clients
ros2 topic list

# Listen to the ESP32 data
ros2 topic echo /scan
ros2 topic echo /data
```

## 📈 Available Topics (with the ESP32)

### From the ESP32 (micro_ros agent):
- `/scan` - LIDAR data from the LD06 sensor
- `/data` - Test counter

### From ROS2 (local nodes):
- `/scan` - LIDAR data published by `talker`
- `/data` - Counter published by `talker`

## 🛠️ Debug and Troubleshooting

### Check the dependencies

```bash
rosdep install --from-paths src --ignore-src -r -y
```

### Build in debug mode

```bash
colcon build --packages-select cpp_pubsub --cmake-args -DCMAKE_BUILD_TYPE=Debug
```

### Raise the log level

```bash
# Terminal 1
ROS_LOG_LEVEL=DEBUG ros2 run cpp_pubsub talker

# Terminal 2
ROS_LOG_LEVEL=DEBUG ros2 run cpp_pubsub listener
```

### Check the build errors

```bash
colcon build --packages-select cpp_pubsub --event-handlers console_cohesion+
```

## 📚 Message Formats

### LaserScan
```cpp
std_msgs/Header header
  uint32 seq
  time stamp
  string frame_id

float32 angle_min          # Min angle (rad)
float32 angle_max          # Max angle (rad)
float32 angle_increment    # Angle increment (rad)
float32 time_increment     # Time between points
float32 scan_time          # Scan duration
float32 range_min          # Min valid distance
float32 range_max          # Max valid distance
float32[] ranges           # Distances (m)
float32[] intensities      # Signal strengths
```

### Int32
```cpp
int32 data  # Counter value
```

## 🔄 Data Pipeline

```
ESP32 (LIDAR LD06)
  │
  └─ micro_ros Agent
      │
      └─ ROS2 Network
          │
          ├─ /scan (LaserScan)
          │   └─ Subscriber displays data
          │   └─ RViz visualization
          │
          └─ /data (Int32 counter)
              └─ Subscriber displays counter
```

## 🎯 Use Cases

1. **Simple visualisation:**
   ```bash
   ros2 run cpp_pubsub talker &
   ros2 run cpp_pubsub listener
   ```

2. **RViz visualisation:**
   ```bash
   ros2 run cpp_pubsub talker &
   rviz2
   ```

3. **With the ESP32:**
   ```bash
   # Terminal 1: Agent
   docker run ... micro_ros_agent ...
   
   # Terminal 2: ROS2 nodes
   ros2 launch cpp_pubsub agent_launch.py
   
   # Terminal 3: RViz
   rviz2 -d ... lidar.rviz
   ```

## 📝 Next Steps

- [ ] Record the LIDAR data (rosbag)
- [ ] Implement a Kalman filter
- [ ] Add an obstacle-avoidance node
- [ ] Create a ROS service for configuration
- [ ] Integrate autonomous navigation

## 🐛 Common Problems

| Problem | Solution |
|---------|----------|
| Topics not listed | `colcon build` and `source install/setup.bash` |
| RViz shows nothing | Check frame_id = "lidar_link" |
| No ESP32 data | Check the WiFi connection + UDP agent |
| Build fails | `rosdep install --from-paths src` |

---

**Date:** 2026-01-19  
**ROS Version:** Humble  
**Python:** 3.10+
