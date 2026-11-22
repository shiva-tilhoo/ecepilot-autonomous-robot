# 🎯 Complete Guide - 360° LIDAR Visualisation with RViz

## ✅ Changes Made

### 1. **ESP32 (main.cpp) - Circular Buffer**
- ✨ **Circular buffer** of 720 points (60 frames × 12 points)
- 📡 **Stores ALL the raw LIDAR points** (even low-confidence ones)
- 🔄 Continuous filling with automatic wrap-around
- 📦 Published directly as a 360° LaserScan

**Characteristics:**
```cpp
#define LIDAR_BUFFER_SIZE 720  // 60 frames of data

typedef struct {
    float angle[LIDAR_BUFFER_SIZE];        // Angle in degrees
    float distance[LIDAR_BUFFER_SIZE];     // Distance in metres
    uint8_t confidence[LIDAR_BUFFER_SIZE]; // Confidence 0-255
    int head;                              // Write index
    int count;                             // Number of points stored
} LidarCircularBuffer;
```

### 2. **ROS2 Listener (publisher_member_function.cpp)**
- 📊 **Callbacks for /scan and /data**
- 📈 Statistics display: min, max, average distance
- 🎯 Log of the first 10 points with angle and distance
- 📝 Clear, informative messages

### 3. **Launch File (agent_launch.py)**
- 📋 **Built-in usage guide**
- 🎨 **Complete RViz instructions**
- 📡 **Display of the received topics**
- 💡 **Usage tips**

### 4. **RViz Configuration (lidar.rviz)**
- 🔴 **Red points** (Flat Color)
- 📏 **Point size**: 8cm (visible)
- 🔍 **Decay Time**: 0.5s (visual trail)
- 📐 **XY grid** for orientation
- 🎯 **Tuned 3D view** (distance 15m, angle 45°)

---

## 🚀 Build and Launch Procedure

### Step 1: Build the ROS2 code

```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source install/setup.bash
colcon build --packages-select cpp_pubsub
source install/setup.bash
```

### Step 2: Upload the code to the ESP32

**With PlatformIO:**
```bash
cd milestones/01_lidar_imu_telemetry/firmware
pio run -t upload
```

Or through the PlatformIO interface in VS Code.

### Step 3: Start the micro-ROS agent (Terminal 1)

```bash
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

### Step 4: Start the listener + RViz (Terminal 2)

```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source install/setup.bash
ros2 launch cpp_pubsub agent_launch.py
```

---

## 🎨 RViz Configuration for the Best Visualisation

The configuration is **already tuned** in `lidar.rviz`, but here is how to change it if needed:

### Adjusting the point size:
1. Open RViz
2. Left panel → **Displays** → **LaserScan**
3. Change **Size (m)**: from 0.05 to 0.15 (for example)
4. Click **Save Config**

### Changing the colour:
1. **LaserScan** → **Color Transformer**: switch from "Flat Color" to "Intensity" or "Range"
2. Adjust **Color** when in "Flat Color" mode

### Showing the history of the points (trail):
1. **LaserScan** → **Decay Time**: change from 0.5 to 2.0 seconds
2. Old points fade progressively

### For a better 3D view:
1. Use the **SCROLL** wheel to zoom
2. **Right-click + drag** to rotate the view
3. **Left-click + drag** to pan

---

## 📡 Topics and Messages

### `/scan` topic (LaserScan)
```
sensor_msgs/LaserScan
├─ header
│  ├─ frame_id: "lidar_link"
│  └─ stamp: timestamp
├─ angle_min: 0.0
├─ angle_max: 6.283 rad (360°)
├─ angle_increment: 0.01745 rad (~1°)
├─ range_min: 0.06m
├─ range_max: 12.0m
├─ ranges[360]: distance for each degree
└─ intensities: empty
```

### `/data` topic (Int32)
```
std_msgs/Int32
└─ data: incremented counter
```

---

## 🔍 Troubleshooting

### ❌ RViz shows "Fixed Frame Error"
**Solution:** make sure the ESP32 is publishing (connected to the agent)

### ❌ No point shows up
1. Check that the agent is running: `docker ps`
2. Check that the ESP32 sends data:
   ```bash
   ros2 topic echo /scan --count 1
   ```
3. Check the ESP32 WiFi connection

### ❌ The points appear white/grey
**Solution:** in RViz, change **Color Transformer** from "Intensity" to "Flat Color"

### ❌ The points only show up over part of the circle
**Solution:** this is normal when only part of the surroundings returns valid measurements. Check that:
- `angle_max - angle_min` matches the expected field of view
- The points are in the `ranges[360]` array

---

## 📊 Reading the Listener Logs

When the listener receives data:
```
[INFO] LIDAR Data: 145/360 points valid | Min: 0.25m | Max: 5.67m | Avg: 3.45m | Angle range: 180°
```

This means:
- ✅ 145 points out of 360 have a valid distance
- 📏 Closest distance: 0.25m, farthest: 5.67m
- 📐 Total angle: 180°

---

## 🛠️ Key Integration Points

### Circular buffer (main.cpp)
```cpp
// Every point is stored here:
static volatile LidarCircularBuffer lidar_buffer;

// For each LIDAR point:
lidar_buffer.angle[lidar_buffer.head] = angle_deg;
lidar_buffer.distance[lidar_buffer.head] = dist_m;
lidar_buffer.confidence[lidar_buffer.head] = conf;
lidar_buffer.head = (lidar_buffer.head + 1) % LIDAR_BUFFER_SIZE;
```

### Publishing (main.cpp)
```cpp
// Go through ALL the points of the buffer and place them over 360°
for(int i = 0; i < lidar_buffer.count; i++) {
    int idx = (int)(lidar_buffer.angle[i]) % 360;
    msg_lidar.ranges.data[idx] = lidar_buffer.distance[i];
}
```

### Reception (publisher_member_function.cpp)
```cpp
// Count the received points
for(size_t i = 0; i < msg->ranges.size(); i++) {
    if(msg->ranges[i] > msg->range_min && msg->ranges[i] < msg->range_max) {
        points_detected++;
    }
}
```

---

## 🎯 Summary of the Improvements

| Before | After |
|--------|-------|
| ❌ Only the 12 points of the last frame | ✅ **720 points** in a circular buffer |
| ❌ Impossible to see every angle | ✅ **360 points** in the LaserScan |
| ❌ No data validation | ✅ **Validation + complete logging** |
| ❌ Generic RViz configuration | ✅ **Tuned 3D configuration** |
| ❌ No user feedback | ✅ **Built-in guide + tips** |

---

## 📝 Optional Next Steps

1. **Add intensities** to colour by confidence:
   ```cpp
   msg_lidar.intensities.data = (float*)malloc(360 * sizeof(float));
   msg_lidar.intensities.data[idx] = (float)confidence;
   ```

2. **Filter low-confidence points** in ROS2:
   ```cpp
   if(lidar_buffer.confidence[i] < 50) continue; // Skip
   ```

3. **Export the data** to a file for analysis:
   ```bash
   ros2 bag record /scan
   ```

4. **Add a point cloud node** for full 3D:
   ```bash
   ros2 run pointcloud_to_laserscan pointcloud_to_laserscan_node
   ```

---

**Configuration complete: the 360 LIDAR points are now visible in real time in RViz.**
