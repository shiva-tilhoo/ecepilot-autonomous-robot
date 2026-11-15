# 🚀 Quick Start

Getting started quickly with the **simulation** and the **real robot**.

---

## ⚡ Option 1: Simulation (2 minutes)

### Setup
```bash
# 1. Activate the Python environment
source .venv/bin/activate

# 2. Source ROS2
source /opt/ros/humble/setup.bash

# 3. Launch the simulation stack
./start_auto_slam_only.sh
```

### Controls
- **Pygame window** (the simulator)
  - `A`: toggle autonomous mode
  - `↑↓←→`: manual commands
  - `Q`: quit

### Visualisation (optional)
```bash
# Terminal 2
rviz2
```
- Fixed Frame: `map`
- Add layers: LaserScan (`/scan`), OccupancyGrid (`/map`)

---

## ⚡ Option 2: Real Robot

### Requirements
✓ ESP32 flashed with the firmware (`platformio.ini`)
✓ LIDAR connected (GPIO16 RX, GPIO25 PWM)
✓ working USB or WiFi connection

### Start-up
```bash
# 1. Environment
source .venv/bin/activate
source /opt/ros/humble/setup.bash

# 2. Launch the stack
./start_robot_mapping_auto.sh

# The script waits for /scan_raw for 15 s
# The ESP32 must start publishing quickly
```

### Checks
```bash
# Terminal 2 - Check the topics
ros2 topic list | grep -E 'scan|odom|map'

# Listen to the scans
ros2 topic echo /scan --max-count=1

# Monitor the map
ros2 topic echo /map --max-count=1
```

---

## 📋 Checklist

### Simulation
- [ ] Python venv activated
- [ ] ROS2 sourced
- [ ] Pygame window shows up
- [ ] Topics `/scan`, `/odom` are published (check with `ros2 topic list`)

### Real Robot
- [ ] ESP32 flashed and connected
- [ ] LIDAR powered and connected
- [ ] `/scan_raw` published by the ESP32 (check: `ros2 topic list`)
- [ ] The script waits, then starts SLAM

---

## 🔧 Stopping the Stack

```bash
# Option 1: Ctrl+C in the main terminal

# Option 2: kill every process
pkill -9 -f 'simu_|slam|restamper|transform'

# Option 3: specific processes
pkill -f slam_toolbox
pkill -f scan_restamper
pkill -f motor_odom_simple
```

---

## 🐛 Common Problems

### "QUICKSTART: Command not found"
```bash
# Find the right path
pwd
ls start_auto_slam_only.sh

# Or use the path from the repository root
ros2/start_auto_slam_only.sh
```

### Simulation: "No module named pygame"
```bash
source .venv/bin/activate
pip install pygame
```

### Robot: "/scan_raw timeout"
```bash
# Check the ESP32
ros2 topic list | grep scan

# If missing:
# 1. Check the USB connection
# 2. Check the baud rate (usually 115200)
# 3. Check that the ESP32 is running the firmware
```

### SLAM does not start
```bash
# Check the slam_toolbox installation
ros2 pkg list | grep slam

# Reinstall if missing
sudo apt install ros-humble-slam-toolbox
```

---

## 📚 Going Further

- **Advanced simulation**: edit `simu_lidar_auto.py` to change the track
- **Autonomous robot**: uncomment `wall_centering_node.py` in `start_robot_mapping_auto.sh`
- **SLAM configuration**: edit `config/slam_corridor_slam_only.yaml` or `config/slam_toolbox_minimal.yaml`

---

**See the `README.md` of the `ros2/` folder for the full documentation.**
