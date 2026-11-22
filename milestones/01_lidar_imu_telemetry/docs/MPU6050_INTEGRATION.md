# MPU6050 Integration - LIDAR + IMU Fusion

## 📋 Overview

This project combines:
- **360° LIDAR** (published on `/scan`)
- **MPU6050 IMU** (published on `/imu/data`)
- **Sensor fusion** in ROS2 + Foxglove

## 🔌 Wiring

### ESP32 ↔ MPU6050
| Signal | ESP32 Pin | MPU6050 Pin |
|--------|-----------|-------------|
| SDA    | GPIO 21   | SDA         |
| SCL    | GPIO 22   | SCL         |
| GND    | GND       | GND         |
| VCC    | 3.3V      | VCC         |
| AD0    | GND       | (I2C address: 0x68) |

### ESP32 ↔ LIDAR
| Signal | ESP32 Pin | LIDAR Pin |
|--------|-----------|-----------|
| TX     | GPIO 17   | RX        |
| RX     | GPIO 16   | TX        |
| GND    | GND       | GND       |
| VCC    | 5V        | VCC       |

## 📦 Architecture

```
ESP32
├── LIDAR Serial2 (115200 baud)
│   └── Publishes: /scan (720 points @ 10Hz)
├── MPU6050 I2C (400kHz)
│   ├── Acceleration (±2g)
│   ├── Gyroscope (±250°/s)
│   └── Publishes: /imu/data (20Hz)
└── microROS Agent
    └── UDP Port 8888

ROS2 Humble
├── /imu/data (sensor_msgs/Imu)
├── /scan (sensor_msgs/LaserScan)
├── /tf (transforms)
└── Foxglove Bridge (port 8765)
```

## 🚀 Getting Started

### 1. Build the Firmware
```bash
cd milestones/01_lidar_imu_telemetry/firmware
platformio run --target upload
```

**Wait for the logs:**
```
[SETUP] Initialisation ESP32 + LIDAR + MPU6050 + microROS
[I2C] Initialisation...
[MPU6050] Detected and initialised!
[LIDAR] Serial2 initialised
[SETUP] ✓ All components initialised!
```

### 2. Start ROS2 (4 Terminals)

**T1 - microROS agent:**
```bash
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

**T2 - Foxglove Bridge:**
```bash
source /opt/ros/humble/setup.bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765
```

**T3 - Sensor Fusion Listener:**
```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source /opt/ros/humble/setup.bash && source install/setup.bash
ros2 run cpp_pubsub sensor_fusion_listener
```

**T4 - Foxglove UI:**
```bash
foxglove-studio
# Connection: ws://localhost:8765
```

## 📊 Topics

### /imu/data (20 Hz)
```bash
geometry_msgs/msg/Vector3 linear_acceleration
  float64 x  # m/s²
  float64 y
  float64 z

geometry_msgs/msg/Vector3 angular_velocity
  float64 x  # rad/s
  float64 y
  float64 z

float64[9] linear_acceleration_covariance
float64[9] angular_velocity_covariance
```

View it:
```bash
ros2 topic echo /imu/data
ros2 topic hz /imu/data
```

### /scan (10 Hz)
```bash
float32[] ranges      # Distance (m) for each angle
float32[] intensities # Intensity (0-1)
float32 angle_min     # 0 rad
float32 angle_max     # 2π rad
float32 angle_increment # 2π/720 ≈ 0.00873 rad
```

View it:
```bash
ros2 topic echo /scan --max-count=1
```

## 🔧 Foxglove Configuration

1. **Open Foxglove**
   ```
   ws://localhost:8765
   ```

2. **Add a 3D panel**
   - Plus (+) → 3D

3. **Topics to display:**
   - ✓ `/scan` → LaserScan (point cloud)
   - ✓ `/imu/data` → (optional, shows the acceleration)
   - ✓ `/tf` → Transforms

4. **Set up the view:**
   - Frame: "map"
   - Target: "lidar"
   - Point size: 5-8px

## 📈 MPU6050 Data

### Calibration (optional)
```bash
# Acceleration at rest ≈ [0, 0, 9.81] m/s²
# Gyroscope at rest ≈ [0, 0, 0] rad/s
# Temperature: see the ESP32 logs
```

### LSB → SI conversion
**Acceleration (±2g):**
- 1g = 9.81 m/s²
- 1 LSB = 9.81 / 16384 m/s² ≈ 0.000599 m/s²

**Gyroscope (±250°/s):**
- 1°/s = π/180 rad/s ≈ 0.01745 rad/s
- 1 LSB = π/(180 × 131) rad/s ≈ 0.000133 rad/s

**Temperature:**
```
T(°C) = (raw_temp + 12412) / 340
```

## 🐛 Debugging

### Check the topics
```bash
ros2 topic list
# Must list: /imu/data, /scan, /tf, etc.
```

### Check the nodes
```bash
ros2 node list
# Must list: /esp32_sensor_fusion, /micro_ros_agent, etc.
```

### Check the data
```bash
ros2 topic echo /imu/data
ros2 topic echo /scan --max-count=1
```

### No data?
1. Check that the microROS agent is running
2. Check the I2C wiring (SDA=21, SCL=22)
3. Check that the MPU6050 is detected:
   ```bash
   # On the ESP32, look at the Serial logs:
   # [MPU6050] Detected and initialised!
   ```
4. Check the rate with `ros2 topic hz /imu/data`

## 📝 Source Code

### ESP32 firmware
- `firmware/src/main.cpp` - IMU + LIDAR publishing

### ROS2 node
- `ros2_ece_ws/src/cpp_pubsub/src/sensor_fusion_listener.cpp` - Reception + display

## 🔗 Resources

- [MPU6050 Datasheet](https://www.uctronics.com/download/Arduino/MPU6050.pdf)
- [microROS with MPU6050](https://github.com/micro-ROS/micro_ros_arduino)
- [ROS2 sensor_msgs/Imu](https://github.com/ros2/common_interfaces/blob/humble/sensor_msgs/msg/Imu.msg)
- [Foxglove IMU Plugin](https://foxglove.dev/)

## 📊 Performance

| Sensor | Rate | Bandwidth |
|--------|------|-----------|
| IMU    | 20 Hz | ~2 KB/s   |
| LIDAR  | 10 Hz | ~100 KB/s |
| Total  | -     | ~102 KB/s |

---

**Version:** 1.0  
**Date:** January 2026  
**Status:** Production Ready
