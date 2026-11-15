# microROS ESP32 Firmware - LIDAR 360°

ESP32 firmware publishing 360° LIDAR data through microROS and ROS2.

## 📋 Overview

This firmware implements:
- **Circular buffer** - 720 LIDAR points (360° / 0.5°)
- **LaserScan publishing** - Standard ROS2 format
- **microROS communication** - Over UDP (port 8888)
- **Arduino interface** - Uses the ESP32 Arduino SDK

## ⚙️ Configuration

### File: `platformio.ini`

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
board_microros_transport = serial
board_microros_distro = humble
lib_deps = https://github.com/micro-ROS/micro_ros_platformio
```

**Key parameters:**
- **Platform**: Espressif32 (ESP32)
- **Board**: ESP32-DevKit-C
- **Framework**: Arduino
- **microROS Transport**: Serial (USB)
- **ROS Distro**: Humble (ROS2 compatible)

## 📦 Dependencies

Installed through PlatformIO:
```
micro_ros_platformio        # microROS for PlatformIO
```

## 🔌 Recommended Wiring

| LIDAR sensor | ESP32 | Notes |
|--------------|-------|-------|
| TX | RX2 (GPIO16) | Serial2 |
| RX | TX2 (GPIO17) | Serial2 |
| GND | GND | |
| VCC | 5V | |

See `src/main.cpp` for the Serial2 configuration.

## 🚀 Installation & Build

### Option 1: VS Code + PlatformIO Extension (Recommended)

1. Install the **PlatformIO IDE** extension in VS Code
2. Open this folder in VS Code
3. Click "Build" in the status bar
4. Connect the ESP32 over USB
5. Click "Upload"

### Option 2: PlatformIO CLI

```bash
# Installation
pip install platformio

# Build
platformio run

# Build + upload
platformio run --target upload

# Monitor the serial output
platformio device monitor --port /dev/ttyUSB0 --baud 115200
```

### Option 3: Docker

```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -v /dev:/dev \
  --privileged \
  platformio/platformio-core \
  pio run --target upload
```

## 📝 Main Code

File: `src/main.cpp`

### Structure

```cpp
// Initialisation
setup() {
  // Serial2 configuration
  // microROS initialisation
  // ROS2 node creation
}

// Main loop
loop() {
  // LIDAR read
  // LaserScan publishing
  // microROS handling
}
```

### Key points of the code

1. **Circular buffer** - Efficient storage of the 720 points
2. **Publishing time** - Timestamp handling
3. **Reference frame** - "lidar" for RViz
4. **Error handling** - Automatic reconnection

## 🔍 Debugging

### Monitoring the serial output

```bash
platformio device monitor --port /dev/ttyUSB0 --baud 115200
```

### Debug messages

The firmware prints:
```
[microROS] Connecting to agent...
[microROS] Connected!
[LIDAR] Publishing: 720 points @ 10Hz
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| LIDAR points | 720 |
| Angular resolution | 0.5° |
| Publishing rate | ~10 Hz |
| Latency | <100ms |
| Bandwidth | ~200 KB/s |
| RAM used | ~150 KB |
| Flash used | ~400 KB |

## 🔧 Modifying the Code

### Changing the resolution

```cpp
// In src/main.cpp
#define LIDAR_POINTS 720  // Change this value
```

### Changing the publishing rate

```cpp
// In src/main.cpp
#define PUBLISH_FREQ_HZ 10  // Change the rate
```

### Adding more sensors

1. Edit the code in `src/main.cpp`
2. Build: `platformio run`
3. Upload: `platformio run --target upload`

## ⚡ Available GPIO Pins

| Port | Use |
|------|-----|
| GPIO16 (RX2) | Serial2 RX |
| GPIO17 (TX2) | Serial2 TX |
| GPIO4 | Free GPIO |
| GPIO12 | Free GPIO |
| GPIO13 | Free GPIO |
| GPIO14 | Free GPIO |

## 🐛 Troubleshooting

### Serial port not found
```bash
# List the ports
ls /dev/tty*

# Check the permissions
sudo usermod -a -G dialout $USER
newgrp dialout
```

### Upload fails
```bash
# Check the FTDI/CH340 drivers
# Install the drivers for the ESP32 if needed
```

### No microROS connection
1. Check that the microROS agent is running
2. Check the UDP port (8888)
3. Check the network connection

## 📚 Resources

- [PlatformIO Documentation](https://docs.platformio.org/)
- [microROS for PlatformIO](https://github.com/micro-ROS/micro_ros_platformio)
- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [ROS2 LaserScan Message](http://docs.ros.org/en/humble/p/sensor_msgs/interfaces/msg/LaserScan.html)

## 🔄 Firmware Update

```bash
# Pull latest changes
git pull

# Rebuild
platformio run

# Upload new version
platformio run --target upload
```

## 📄 Important Files

| File | Description |
|------|-------------|
| `src/main.cpp` | Main firmware code |
| `platformio.ini` | Project configuration |
| `include/` | Headers (external libraries) |
| `lib/` | Local dependencies |

---

**Last update:** January 2026  
**Firmware version:** 1.0.0  
**Compatible with:** ROS2 Humble, microROS
