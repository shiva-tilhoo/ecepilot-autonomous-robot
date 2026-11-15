# ✅ RVIZ - COMPLETE SOLUTION

## Problem Identified
```
rviz2: symbol lookup error: /snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0: 
undefined symbol: __libc_pthread_init, version GLIBC_PRIVATE
```

### Root Cause
VS Code (snap) pollutes the environment variables:
- `XDG_DATA_HOME` → `~/snap/code/...`
- `GTK_PATH` → `/snap/code/219/usr/lib/x86_64-linux-gnu/gtk-3.0`
- Several other "VSCODE_SNAP_ORIG" variables

This forces RViz to look for its dependencies in `/snap/core20/` instead of `/usr/lib/`.

## Solution Implemented

### 1. Wrapper Script (`run_rviz.sh`)
Creates a clean environment by neutralising the VS Code snap variables:

```bash
#!/bin/bash
# Clear every VS Code snap variable
unset XDG_DATA_HOME
unset GSETTINGS_SCHEMA_DIR
unset GTK_PATH
unset GTK_EXE_PREFIX
# ... etc (18 variables cleared)

# Restore the right PATH (without snap)
export PATH="/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Source ROS
source /opt/ros/humble/setup.bash

# Start RViz
exec rviz2 "$@"
```

**Location:** `milestones/01_lidar_imu_telemetry/ros2_ece_ws/run_rviz.sh`

### 2. Integration in the Launch File
**File:** `src/cpp_pubsub/launch/agent_launch.py`

Change:
```python
# BEFORE: direct Node (broken by snap)
Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    output='screen',
),

# AFTER: ExecuteProcess with the wrapper script (clean)
ExecuteProcess(
    cmd=['milestones/01_lidar_imu_telemetry/ros2_ece_ws/run_rviz.sh'],
    output='screen',
),
```

## Usage

### Option 1: Start RViz alone (quick test)
```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
./run_rviz.sh
```

### Option 2: Start with agent_launch.py (complete)
```bash
# Terminal 1: micro_ros agent
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888

# Terminal 2: launch file + listener + RViz
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source install/setup.bash
ros2 launch cpp_pubsub agent_launch.py
```

## Checks
```bash
ps aux | grep rviz2          # See RViz running
cat /tmp/rviz.log            # Start-up logs
```

## Wayland Warning
```
Warning: Ignoring XDG_SESSION_TYPE=wayland on Gnome. 
Use QT_QPA_PLATFORM=wayland to run on Wayland anyway.
```

→ **Normal and can be ignored.** RViz starts correctly in X11 fallback mode.

## Advanced Debugging (if it still fails)
```bash
# See exactly which dependencies RViz loads
ldd $(which rviz2) | grep snap    # Should be EMPTY

# Check the RViz environment
milestones/01_lidar_imu_telemetry/ros2_ece_ws/run_rviz.sh --verbose

# Run RViz with strace to see the system calls
strace -e open,openat milestones/01_lidar_imu_telemetry/ros2_ece_ws/run_rviz.sh 2>&1 | grep pthread
```

## RViz Configuration for LaserScan
1. In RViz, click **"Add"** → **"By topic"** → select `/scan` (LaserScan)
2. Adjust the display parameters:
   - **Color transformer**: Intensity
   - **Style**: Points or Spheres
   - **Decay time**: 0.2s (to see the history)

## Status ✅
- ✅ RViz starts without the snap error
- ✅ To be integrated in the launch file
- ✅ Ready for real-time LIDAR visualisation
