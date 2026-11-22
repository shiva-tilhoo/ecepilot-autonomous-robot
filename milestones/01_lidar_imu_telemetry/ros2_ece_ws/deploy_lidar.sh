#!/bin/bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # directory of this script

# Full build and deployment check script
# Usage: ./deploy_lidar.sh

set -e  # Exit on error

echo "========================================"
echo "🚀 LIDAR 360° build - full system"
echo "========================================"
echo ""

# ============ STEP 1: Build ROS2 ============
echo "📦 [1/3] Building ROS2..."
cd "$HERE"

source install/setup.bash 2>/dev/null || source /opt/ros/humble/setup.bash
echo "   ✓ ROS2 environment sourced"

colcon build --packages-select cpp_pubsub 2>&1 | grep -E "(error|warning|Compiling|Linking)" || echo "   ✓ ROS2 build succeeded"
source install/setup.bash
echo "   ✓ ROS2 code built successfully"
echo ""

# ============ STEP 2: Check the ESP32 code ============
echo "💾 [2/3] Checking the ESP32 code..."
cd "$HERE/../firmware"

if ! grep -q "LidarCircularBuffer" src/main.cpp; then
    echo "   ✗ Error: circular buffer not found!"
    exit 1
fi
echo "   ✓ Circular buffer: OK"

if ! grep -q "LIDAR_BUFFER_SIZE 720" src/main.cpp; then
    echo "   ✗ Error: invalid buffer size!"
    exit 1
fi
echo "   ✓ Buffer size: 720 points (60 frames)"

if ! grep -q "rcl_publish(&pub_lidar" src/main.cpp; then
    echo "   ✗ Error: LIDAR publication not found!"
    exit 1
fi
echo "   ✓ Publication LaserScan: OK"
echo ""

# ============ STEP 3: Check the config files ============
echo "⚙️  [3/3] Checking the configuration files..."
cd "$HERE/src/cpp_pubsub/launch"

if ! grep -q "LaserScan 360" lidar.rviz; then
    echo "   ✗ Error: RViz configuration not updated!"
    exit 1
fi
echo "   ✓ RViz configuration: OK (360 points, red)"

if ! grep -q "360 LIDAR points" agent_launch.py; then
    echo "   ✗ Error: launch guide not updated!"
    exit 1
fi
echo "   ✓ Launch guide: OK"

echo ""
echo "========================================"
echo "✅ LIDAR 360° system ready to launch!"
echo "========================================"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  Terminal 1 - Start the micro-ROS agent:"
echo "   docker run -it --rm microros/micro-ros-docker:humble \\"
echo "     ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888"
echo ""
echo "2️⃣  Terminal 2 - Flash the ESP32 code (PlatformIO)"
echo "   Open: $HERE/../firmware"
echo "   Click 'Upload' in PlatformIO"
echo ""
echo "3️⃣  Terminal 3 - Start the listener + RViz:"
echo "   cd $HERE"
echo "   source install/setup.bash"
echo "   ros2 launch cpp_pubsub agent_launch.py"
echo ""
echo "🎨 RViz will show:"
echo "   • Grey XY grid (reference)"
echo "   • LIDAR points in red (360 points)"
echo "   • Fixed frame: lidar_link"
echo ""
echo "📖 See the full guide: LIDAR_360_GUIDE.md"
echo ""
