# 🎨 RVIZ Instructions - LIDAR 360° Visualisation

## 📍 Overview

When `ros2 launch cpp_pubsub agent_launch.py` is started, RViz opens **automatically** with a configuration tuned to display the 360 LIDAR points.

---

## ✅ Automatic Setup

The RViz configuration is **pre-configured** with:
- ✓ Grey **XY grid** in the background (spatial reference)
- ✓ **LIDAR points** in **red** (highly visible)
- ✓ **360 points** displayed at once
- ✓ Fixed **frame**: `lidar_link`
- ✓ Tuned **3D view** (distance 15m, angle 45°)

**Normally there is nothing to do.** The config is applied automatically.

---

## 🎯 If Manual Adjustment Is Needed

### Case 1: The points do not show up

**Step 1:** check that the agent is running
```bash
docker ps | grep micro-ros-agent
```

If nothing is listed → start the agent:
```bash
docker run -it --rm microros/micro-ros-docker:humble \
  ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

**Step 2:** check the topics
```bash
ros2 topic list
```

You must see:
```
/scan
/data
```

**Step 3:** check the received data
```bash
ros2 topic echo /scan --count 1
```

The LaserScan fields should be printed.

---

### Case 2: RViz shows "No Transform available"

**Solution:** this is normal during the first 5 seconds. Wait.

If the message persists:
1. In RViz, go to **Global Options** (left panel)
2. **Fixed Frame**: choose **lidar_link**
3. Click **OK**

---

### Case 3: Making the points bigger

1. Left panel → **Displays**
2. Click **LaserScan (Tous les 360 points)**
3. Find **Size (m)**: change it from **0.08** to **0.15** (or more)
4. The points get bigger immediately

---

### Case 4: Changing the colour

**Option A: Keep a fixed colour**
1. **LaserScan** → **Color Transformer**: stay on **Flat Color**
2. Click **Color**: pick the desired colour
3. Click **OK**

**Option B: Colour by distance (red = close, blue = far)**
1. **Color Transformer**: choose **Range**
2. The points gradually turn red/green/blue depending on the distance

**Option C: Colour by confidence**
1. First, build with intensities:
   ```cpp
   // In the ESP32 main.cpp, publish section:
   msg_lidar.intensities.size = 360;
   msg_lidar.intensities.data = (float*)malloc(360 * sizeof(float));
   for(int i = 0; i < 360; i++) {
       msg_lidar.intensities.data[i] = (float)lidar_buffer.confidence[i];
   }
   ```
2. Rebuild and upload
3. In RViz: **Color Transformer** → **Intensity**

---

### Case 5: Showing the history of the points (trail)

1. **LaserScan** → **Decay Time**: change it from **0.5** to **2.0** seconds
2. Old points will fade slowly

To keep them longer: use **5.0**

---

### Case 6: The 3D view is oddly oriented

**Reset the view:**
1. Right panel → **Views**
2. Under **Current View**, click **View Type**: choose **XYOrbit**
3. Set:
   - **Distance**: 15m
   - **Pitch**: 0.65 rad (≈37°)
   - **Yaw**: 0.785 rad (45°)

**Or simply:**
1. Press **Home** on the keyboard
2. RViz restores the default view

---

## 🎮 RViz Controls

| Action | Keyboard/Mouse |
|--------|----------------|
| Zoom | **Scroll** up/down |
| Rotate the view | **Right-click** + drag |
| Pan | **Right-click + Shift** + drag |
| Select a point | **Left-click** |
| Measure a distance | **Measure** tool (toolbar) |

---

## 📊 Reading the Displays

### In RViz:

```
┌─────────────────────────────────┐
│ Global Options                  │
├─────────────────────────────────┤
│ ✓ Fixed Frame: lidar_link       │
│ ✓ Background: grey (48,48,48)   │
│ ✓ Frame Rate: 30Hz              │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Displays                        │
├─────────────────────────────────┤
│ ✓ Grid (grey, alpha 0.3)        │
│ ✓ LaserScan (red, 360 points)   │
│   - Size: 8cm                   │
│   - Decay: 0.5s                 │
│   - Color: Red                  │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Terminal Output:                │
├─────────────────────────────────┤
│ [INFO] LIDAR Data: 145/360      │
│ points valid | Min: 0.25m       │
│ Max: 5.67m | Avg: 3.45m         │
└─────────────────────────────────┘
```

**Interpretation:**
- ✅ 145 points have a valid distance (between 0.06m and 12m)
- 📏 Closest point: 25cm
- 📏 Farthest point: 5.67m
- 📏 Average distance: 3.45m

---

## 🔍 Advanced Troubleshooting

### The points jump around

**Cause:** the circular buffer is still filling
**Solution:** wait for 60 frames (about 2 seconds) until the buffer is completely filled

### There are "holes" in the scan

**Cause:** this is normal when only part of the surroundings returns a valid measurement
**Check:** 
```bash
ros2 topic echo /scan | grep "angle_max"
```
It will probably show: `angle_max: 3.14` (π radians = 180°)

### The points are very far (>10m) or very close (<5cm)

**Cause:** check that the LIDAR communicates properly
**Debug:**
```bash
# ESP32 terminal:
Serial Monitor of the LIDAR
You must see: [LIDAR] Task started on core 1
```

---

## 💾 Saving the RViz Configuration

After adjusting the parameters:

**Method 1: Automatically**
- RViz saves automatically when it is closed
- The first time, click **Panels** → **Save Config As**

**Method 2: Manually**
```bash
# Export the current config
ros2 run rviz2 rviz2 -d lidar.rviz --save-display-config
```

---

## 📝 Key Points to Remember

✅ **Automatic configuration** → no manual setup needed
✅ **360 points displayed** → the whole area around the LIDAR is visible
✅ **Red points** → easy to see on a grey background
✅ **Frame: lidar_link** → the reference frame of the LIDAR
✅ **Zoom with scroll** → easy control
✅ **0.5s trail** → shows how the points move

---

## 🎬 Quick Workflow

1. **Terminal 1:**
   ```bash
   docker run -it --rm microros/micro-ros-docker:humble \
     ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
   ```

2. **Terminal 2:**
   ```bash
   cd milestones/01_lidar_imu_telemetry/ros2_ece_ws
   source install/setup.bash
   ros2 launch cpp_pubsub agent_launch.py
   ```

3. **RViz opens automatically** with the 360 points in red ✓

4. **Watch terminal 2** for the LIDAR statistics

5. **Adjust if needed** with the RViz keys/mouse

---

## ❓ Frequently Asked Questions

**Q: Why are the points red and not another colour?**
A: On purpose: red stands out on the grey background. It can be changed by following case 4.

**Q: How many points should be visible?**
A: Between 100 and 360 depending on the geometry around the LIDAR. 360 points when every angle gets a detection.

**Q: Why a 0.5s decay and not 0?**
A: It shows how obstacles move. Adjust Decay Time if needed.

**Q: Nothing shows up within 0.06m of the LIDAR - is that normal?**
A: Yes, it is the "dead zone" of the sensor. It cannot detect anything closer than 6cm.

---

## 🎓 Next Steps

Now that RViz works:

1. **Test confidence filtering** in ROS2
2. **Export as a point cloud** for 3D mapping
3. **Integrate with SLAM** for localisation
4. **Build an occupancy map** for navigation

See the "Next steps" section of **GUIDE_LIDAR_360_COMPLET.md**
