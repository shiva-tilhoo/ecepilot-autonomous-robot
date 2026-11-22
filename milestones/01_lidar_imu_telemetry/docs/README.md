# ECE ROS2 & microROS Lidar 360° Project

Complete 360° LIDAR visualisation project combining ROS2, microROS and an ESP32 board.

## 📁 Project Structure

```
ros2_ece_ws/                      # Main ROS2 workspace
├── src/
│   ├── cpp_pubsub/               # C++ publish/subscribe node
│   └── vehicle_description/      # URDF description of the vehicle
├── build/                        # Build artefacts
├── install/                      # Installed packages
└── [Documentation and scripts]

firmware/                         # ESP32 microROS firmware
├── src/main.cpp                  # Main code
├── platformio.ini                # PlatformIO configuration
└── [Dependencies and libs]
```

## 🎯 Features

✅ **Circular 360° LIDAR** - ESP32 circular buffer (720 points)  
✅ **ROS2 LaserScan publishing** - Standard, compatible format  
✅ **RViz visualisation** - Pre-tuned configuration  
✅ **microROS communication** - Over UDP  
✅ **Full documentation** - Detailed guides included  

## ⚡ Quick Start

### Requirements

```bash
# ROS2 Humble (Ubuntu 22.04)
curl https://repo.ros2.org/ros.key | sudo apt-key add -
sudo apt update && sudo apt install ros-humble-desktop

# PlatformIO CLI
pip install platformio

# Docker (for the microROS agent)
sudo apt install docker.io
```

### 1. Start the microROS agent (Terminal 1)

```bash
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

### 2. Configure and build the ROS2 workspace (Terminal 2)

```bash
cd ros2_ece_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select cpp_pubsub vehicle_description
source install/setup.bash
```

### 3. Upload the ESP32 firmware (Terminal 3)

```bash
cd firmware
platformio run --target upload
# Or open the folder in VS Code + PlatformIO extension
```

### 4. Start the ROS2 nodes (Terminal 2)

```bash
# Start the listener with statistics
ros2 run cpp_pubsub listener

# Or visualise in RViz from another terminal
ros2 launch rviz2 rviz2 -d ros2_ece_ws/lidar_config.rviz
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [00_FINAL_SUMMARY.md](../ros2_ece_ws/00_FINAL_SUMMARY.md) | Complete project summary |
| [QUICKSTART.md](../ros2_ece_ws/QUICKSTART.md) | 2-minute quick start |
| [LIDAR_360_GUIDE.md](../ros2_ece_ws/LIDAR_360_GUIDE.md) | LIDAR technical guide |
| [RVIZ_CONFIGURATION_GUIDE.md](../ros2_ece_ws/RVIZ_CONFIGURATION_GUIDE.md) | Detailed RViz configuration |
| [MODIFICATIONS_SUMMARY.md](../ros2_ece_ws/MODIFICATIONS_SUMMARY.md) | Change history |

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────┐
│               ROS2 Workspace (Ubuntu)                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │  cpp_pubsub (Listener + Stats)                     │  │
│  │  vehicle_description (URDF)                        │  │
│  │  RViz (Visualisation)                              │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │ ROS2 LaserScan (UDP)
┌──────────────────▼──────────────────────────────────────┐
│         microROS Agent (Docker)                          │
│         Port: 8888                                       │
└──────────────────┬──────────────────────────────────────┘
                   │ micro-XRCE-DDS
┌──────────────────▼──────────────────────────────────────┐
│          ESP32 + LIDAR (microROS)                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  PlatformIO firmware                               │  │
│  │  720-point circular buffer                         │  │
│  │  LaserScan publishing                              │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 📦 ROS2 Packages

- **cpp_pubsub** - LaserScan publish/subscribe
- **vehicle_description** - URDF description of the vehicle

## 🎮 Useful Scripts

```bash
# Build and run
./run_lidar.sh          # Starts listener + stats
./run_rviz.sh           # Starts RViz with the config

# Tests
./test_lidar.sh         # Communication test
./visualize_lidar.py    # Basic Python visualisation

# Configuration
./setup_rviz_display.sh # Configures RViz automatically
./deploy_lidar.sh       # Deploys the whole system
```

## 📊 Technical Specifications

| Parameter | Value |
|-----------|-------|
| LIDAR resolution | 360° / 0.5° = 720 points |
| Publishing rate | ~10 Hz |
| Format | Standard ROS2 LaserScan |
| Communication | UDP (port 8888) |
| Platform | ESP32 |
| Firmware | Arduino + microROS + PlatformIO |

## 🐛 Troubleshooting

### The microROS agent does not start
```bash
docker pull microros/micro-ros-docker:humble
docker run -it --rm microros/micro-ros-docker:humble bash
```

### No LIDAR data
1. Check the USB connection
2. Check the serial port: `ls /dev/tty*`
3. Run the PlatformIO upload again

### RViz displays the data incorrectly
1. Check the "lidar" frame in the RViz configuration
2. See [RVIZ_CONFIGURATION_GUIDE.md](../ros2_ece_ws/RVIZ_CONFIGURATION_GUIDE.md)

## 👤 Authors

Mathéo Léon, Amandine Soyez, Shiva Tilhoo - ECE ROS2 project

## 🔗 Resources

- [ROS2 Documentation](https://docs.ros.org/en/humble/)
- [microROS Documentation](https://micro.ros.org/)
- [PlatformIO Documentation](https://docs.platformio.org/)
- [RViz User Guide](https://wiki.ros.org/rviz)

---

**Last update:** January 2026
