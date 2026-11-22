# 🚀 QUICK INSTALLATION - 5 MINUTES

Guide to set up the ECE ROS2 + microROS LIDAR 360° project quickly.

## 📋 Steps

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/shiva-tilhoo/ecepilot-autonomous-robot.git
cd ecepilot-autonomous-robot/milestones/01_lidar_imu_telemetry
```

### 2️⃣ Install the Dependencies (Optional - Automatic)

```bash
chmod +x setup.sh
./setup.sh
```

**Or install them manually:**

```bash
# ROS2 Humble
sudo apt install ros-humble-desktop ros-humble-rviz2 -y

# PlatformIO
pip install platformio

# Docker (for the microROS agent)
sudo apt install docker.io -y
docker pull microros/micro-ros-docker:humble
```

### 3️⃣ Build the ROS2 Workspace

```bash
cd ros2_ece_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

### 4️⃣ Start the System (3 Terminals)

#### Terminal 1: microROS agent
```bash
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

#### Terminal 2: ROS2 listener
```bash
cd ros2_ece_ws
source install/setup.bash
ros2 run cpp_pubsub listener
```

#### Terminal 3: RViz visualisation
```bash
cd ros2_ece_ws
source install/setup.bash
ros2 launch rviz2 rviz2 -d lidar_config.rviz
```

## 🔌 Uploading the ESP32 Firmware

```bash
cd firmware
platformio run --target upload

# Or from VS Code:
# 1. Open the firmware folder
# 2. Install the PlatformIO extension
# 3. Click "Upload" in the status bar
```

## ✅ Checks

You should see:
- ✅ Terminal 1: agent connected and listening
- ✅ Terminal 2: LIDAR messages published (720 points)
- ✅ Terminal 3: real-time LIDAR visualisation in RViz

## 📚 Documentation

- [README.md](README.md) - Full overview
- [../ros2_ece_ws/QUICKSTART.md](../ros2_ece_ws/QUICKSTART.md) - ROS2 workflow
- [../ros2_ece_ws/LIDAR_360_GUIDE.md](../ros2_ece_ws/LIDAR_360_GUIDE.md) - Technical details

## 🐛 Problems?

```bash
# Check that ROS2 is sourced
echo $ROS_DISTRO  # Should print: humble

# Check the topics
ros2 topic list

# List the active nodes
ros2 node list

# Watch the messages live
ros2 topic echo /scan
```
