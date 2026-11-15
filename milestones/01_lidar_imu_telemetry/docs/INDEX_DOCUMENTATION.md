# 📚 INDEX - Every File of the Milestone

## 🎯 Starting Point - READ THESE FIRST

### 📖 Main Documentation

1. **[README.md](README.md)** ⭐ **READ FIRST**
   - Complete project overview
   - System architecture
   - Quick start (3 steps)
   - Every resource link

2. **[INSTALLATION_RAPIDE.md](INSTALLATION_RAPIDE.md)** 🚀 **5 MINUTES**
   - Very fast setup
   - Automatic installation available
   - Starting the 3 terminals

---

## 📁 Structure of the Milestone

```
milestones/01_lidar_imu_telemetry/
├── docs/                                  ← This documentation
│   ├── README.md                          ← READ FIRST
│   ├── INSTALLATION_RAPIDE.md             ← 5-min setup
│   ├── LIDAR_OPTIMIZATION.md              ← High-speed LIDAR firmware
│   └── MPU6050_INTEGRATION.md             ← IMU integration
│
├── setup.sh                               ← Automatic installation
│   └── Installs ROS2, PlatformIO, Docker
│
├── firmware/                              ← ESP32 firmware
└── ros2_ece_ws/                           ← ROS2 workspace
```

---

## 📂 ROS2 Workspace

### `ros2_ece_ws/` - Main workspace

**ROS2 documentation:**
- [ros2_ece_ws/README.md](../ros2_ece_ws/README.md) - Complete ROS2 view
- [ros2_ece_ws/QUICKSTART.md](../ros2_ece_ws/QUICKSTART.md) - ROS2 quick start
- [ros2_ece_ws/GUIDE_LIDAR_360_COMPLET.md](../ros2_ece_ws/GUIDE_LIDAR_360_COMPLET.md) - LIDAR specifications
- [ros2_ece_ws/GUIDE_RVIZ_CONFIGURATION.md](../ros2_ece_ws/GUIDE_RVIZ_CONFIGURATION.md) - RViz setup

**C++ sources (colcon packages):**
- `src/cpp_pubsub/` - LaserScan publish/subscribe
  - `src/publisher_member_function.cpp` - Publisher
  - `src/subscriber_member_function.cpp` - Subscriber (listener)
  - `src/lidar_buffer_node.cpp` - LIDAR circular buffer
  - [src/cpp_pubsub/README.md](../ros2_ece_ws/src/cpp_pubsub/README.md) - Package docs

- `src/vehicle_description/` - URDF description
  - `urdf/vehicle.urdf` - 3D model of the vehicle

**Configurations:**
- `lidar_config.rviz` - Pre-tuned RViz configuration
- `launch/` - ROS2 launch files

**Launch scripts:**
- `run_lidar.sh` - Starts the listener + stats
- `run_rviz.sh` - Starts RViz with the config
- `test_lidar.sh` - Communication tests
- `deploy_lidar.sh` - Full deployment

**Python visualisation:**
- `lidar_simple_plot.py` - Simple matplotlib plot
- `visualize_lidar.py` - More advanced visualisation

**Detailed documentation:**
- [00_SYNTHESE_FINALE.md](../ros2_ece_ws/00_SYNTHESE_FINALE.md) - Overall summary
- [MODIFICATIONS_SUMMARY.md](../ros2_ece_ws/MODIFICATIONS_SUMMARY.md) - History
- [CHANGEMENTS_DETAILS.md](../ros2_ece_ws/CHANGEMENTS_DETAILS.md) - Detailed changes
- [RESUME_MODIFICATIONS.md](../ros2_ece_ws/RESUME_MODIFICATIONS.md) - Summary
- [INDEX_FICHIERS.md](../ros2_ece_ws/INDEX_FICHIERS.md) - ROS2 file index

---

## 🔧 microROS Firmware

### `firmware/` - ESP32 firmware

**Documentation:**
- [firmware/README.md](../firmware/README.md) - Complete firmware guide
  - PlatformIO configuration
  - Installation & build
  - Recommended wiring
  - Debugging and troubleshooting

**Source code:**
- `src/main.cpp` - Main firmware
  - 720-point circular buffer
  - ROS2 LaserScan publishing
  - microROS UDP communication

**Configuration:**
- `platformio.ini` - Project configuration
  - Platform: espressif32
  - Board: esp32dev
  - Framework: Arduino
  - microROS dependencies

---

## 📊 Navigation Guide by Use Case

### 🚀 I just want to get started quickly

1. [INSTALLATION_RAPIDE.md](INSTALLATION_RAPIDE.md) - 5 min
2. Follow the 4 steps

### 📚 I want to understand the project as a whole

1. [README.md](README.md) - Overview
2. [00_SYNTHESE_FINALE.md](../ros2_ece_ws/00_SYNTHESE_FINALE.md) - Detailed summary
3. Look at the architecture in the README

### 🤖 I want to understand ROS2

1. [ros2_ece_ws/README.md](../ros2_ece_ws/README.md) - ROS2 structure
2. [ros2_ece_ws/QUICKSTART.md](../ros2_ece_ws/QUICKSTART.md) - Workflow
3. [ros2_ece_ws/GUIDE_LIDAR_360_COMPLET.md](../ros2_ece_ws/GUIDE_LIDAR_360_COMPLET.md) - Technical details

### 💻 I want to understand the firmware

1. [firmware/README.md](../firmware/README.md) - Firmware guide
2. Read `src/main.cpp` - Source code
3. Configure `platformio.ini` - Configuration

### 📺 I want to configure RViz

1. [ros2_ece_ws/GUIDE_RVIZ_CONFIGURATION.md](../ros2_ece_ws/GUIDE_RVIZ_CONFIGURATION.md) - RViz guide
2. Use `lidar_config.rviz` - Ready-made config
3. Run `./run_rviz.sh` - Launch script

### 🔧 I want to modify the code

1. Change the source files
2. Build: `colcon build` (ROS2) or `platformio run` (firmware)
3. Test the changes

---

## 📝 Files by Type

### Configuration
- `platformio.ini` - PlatformIO config
- `lidar_config.rviz` - RViz config

### Source Code
- `firmware/src/main.cpp` - ESP32 firmware
- `ros2_ece_ws/src/cpp_pubsub/src/*.cpp` - ROS2 C++ code
- `ros2_ece_ws/src/vehicle_description/urdf/vehicle.urdf` - URDF model

### Scripts
- `setup.sh` - Automatic installation
- `ros2_ece_ws/run_*.sh` - ROS2 launch scripts
- `ros2_ece_ws/*.py` - Python visualisation scripts

### Documentation
- `.md` files - Markdown documentation
  - Detailed guides with examples
  - Troubleshooting and FAQs

---

## 🔍 Quick Search

### By Topic

| Topic | File |
|-------|------|
| Project overview | [README.md](README.md) |
| Installation | [INSTALLATION_RAPIDE.md](INSTALLATION_RAPIDE.md) |
| ROS2 | [ros2_ece_ws/README.md](../ros2_ece_ws/README.md) |
| Firmware | [firmware/README.md](../firmware/README.md) |
| LIDAR | [ros2_ece_ws/GUIDE_LIDAR_360_COMPLET.md](../ros2_ece_ws/GUIDE_LIDAR_360_COMPLET.md) |
| RViz | [ros2_ece_ws/GUIDE_RVIZ_CONFIGURATION.md](../ros2_ece_ws/GUIDE_RVIZ_CONFIGURATION.md) |

### By Level

| Level | Files | Time |
|-------|-------|------|
| Beginner | INSTALLATION_RAPIDE.md | 5 min |
| Intermediate | README.md + specific guides | 30 min |
| Advanced | Source code + specifications | - |

---

## ✅ Onboarding Checklist

- [ ] Read [README.md](README.md)
- [ ] Run `setup.sh` or install manually
- [ ] Build ROS2: `colcon build`
- [ ] Upload the ESP32 firmware: `platformio run --target upload`
- [ ] Start the 3 terminals (agent, listener, RViz)
- [ ] Check the LIDAR data

---

## 🎯 Quick Commands

```bash
# Installation
./setup.sh

# Build ROS2
cd ros2_ece_ws && colcon build && source install/setup.bash

# Run
./run_lidar.sh              # Terminal 2
./run_rviz.sh               # Terminal 3

# Upload firmware
cd firmware && platformio run --target upload
```

---

## 📞 Support

- **ROS2**: https://docs.ros.org/en/humble/
- **microROS**: https://micro.ros.org/
- **PlatformIO**: https://docs.platformio.org/

---

**Last update:** January 2026  
**Code:** complete ROS2 + microROS
