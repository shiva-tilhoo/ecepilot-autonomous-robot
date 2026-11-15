#!/bin/bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # directory of this script
# Start SLAM Stack with Lifecycle Management
# Adapted from ldrobot-lidar-ros2 + optimized for ESP32 setup

set -e

source /opt/ros/humble/setup.bash
source "${MICROROS_WS:-$HOME/microros_ece_ws}/install/setup.bash"

echo "==============================================="
echo "🚀 SLAM Stack (Lifecycle + Nav2 Pattern)"
echo "==============================================="
echo ""
echo "Architecture:"
echo "  • Motor Odometry (100% mode - NO IMU)"
echo "  • Scan Restamper (fix LIDAR timestamps)"
echo "  • Odometry Relay (no fusion)"
echo "  • SLAM Toolbox (async mode)"
echo "  • Nav2 Lifecycle Manager (orchestration)"
echo ""

cd "$HERE"

# Check if agent is running
if ! pgrep -f "micro_ros_agent" > /dev/null; then
  echo "[1/2] Starting Micro-ROS Agent on port 8888..."
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888 &
  AGENT_PID=$!
  sleep 2
else
  echo "[1/2] Micro-ROS Agent already running ✓"
fi

echo ""
echo "[2/2] Launching SLAM Stack with Lifecycle Manager..."
python3 "$HERE/launch/start_stack_lifecycle.launch.py"

# Cleanup on exit
trap "pkill -P $$" SIGINT SIGTERM
wait

echo ""
echo "✓ Stack shutdown complete"
