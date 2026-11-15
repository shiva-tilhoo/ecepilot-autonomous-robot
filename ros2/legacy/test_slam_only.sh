#!/bin/bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # directory of this script
# Ultra simple test: Just SLAM, verify /map is published

set -e
source /opt/ros/humble/setup.bash
source "${MICROROS_WS:-$HOME/microros_ece_ws}/install/setup.bash"

cd "$HERE"

echo "=== STEP 1: Launch SLAM ONLY ==="
echo "Launching SLAM Toolbox..."

ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$(pwd)/config/slam_toolbox_params.yaml \
  autostart:=true use_lifecycle_manager:=false
