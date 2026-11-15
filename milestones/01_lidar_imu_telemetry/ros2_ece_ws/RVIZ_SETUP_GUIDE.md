# DISPLAYING THE LIDAR POINTS IN RVIZ ✅

## Step 1: Start the whole system

Terminal 1 - micro_ros agent:
```bash
cd milestones/01_lidar_imu_telemetry/firmware
source /opt/ros/humble/setup.bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

Terminal 2 - RViz + listener launch:
```bash
cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
source install/setup.bash
ros2 launch cpp_pubsub agent_launch.py
```

## Step 2: Configure RViz MANUALLY

### ⚠️ IMPORTANT: do not load the config directly!

RViz must be configured by hand for this LIDAR because:
- The `lidar_link` frame must be defined correctly
- The topics must be discovered in real time
- The transforms must be valid

### 🎯 Procedure to add the LaserScan:

1. **RViz opens** → the main window is empty

2. **At the bottom left**, click the **"Add"** button 

3. **A dialog opens** → look for **"LaserScan"** in the list
   - Click **"LaserScan by Topic"**

4. **New "LaserScan" window** → in the "Topic" field:
   - Click the white area
   - Select **"/scan"** in the dropdown
   - OR type `/scan` directly

5. **Click OK** → the points should appear! 🎨

### ✅ Recommended RViz configuration:

| Parameter | Value |
|-----------|-------|
| Style | **Spheres** |
| Size (Pixels) | **3-5** |
| Size (m) | **0.05** |
| Color Transformer | **Intensity** or **Rainbow** |
| Decay Time | **0.2** |
| Use rainbow | **Checked** ✓ |
| Queue Size | **10** |

### 🔍 Checking the incoming data:

In a third terminal:
```bash
source /opt/ros/humble/setup.bash
ros2 topic echo /scan --max-count=1
```

You should see a LaserScan output with:
- 360 points
- Angles 0-2π
- Distances in metres

### ❌ If it still does not work:

```bash
# 1. Check that the topic exists
ros2 topic list | grep scan

# 2. Check the data
ros2 topic echo /scan

# 3. Check the frame
ros2 topic echo /scan | grep frame_id

# 4. Restart the listener
pkill -f listener
ros2 run cpp_pubsub listener
```

## 📺 Expected result

- **Coloured points** in the centre of RViz (rainbow gradient)
- **~10-12 points per scan** (sparse LIDAR)
- **Update every ~1 second**
- **Distances usually 0.2-0.6m** (depending on the surroundings)

## 💾 Saving the RViz configuration

Once configured by hand:
1. **File** → **Save As**
2. Name the file: `lidar_setup.rviz`
3. Save it in `milestones/01_lidar_imu_telemetry/ros2_ece_ws/`
4. Next time, load it with:
   ```bash
   rviz2 -d milestones/01_lidar_imu_telemetry/ros2_ece_ws/lidar_setup.rviz
   ```
