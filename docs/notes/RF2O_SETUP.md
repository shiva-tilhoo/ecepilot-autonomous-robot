# SLAM Stack with RF2O - Getting Started

## 📋 Architecture

Full stack with:
- **RF2O**: real-time laser odometry (LIDAR scan matching)
- **Motor Odometry**: motor odometry (fallback)
- **Fusion**: 80% RF2O + 20% Motor
- **SLAM Toolbox**: mapping with loop closure

## 🚀 Launch

```bash
cd ros2
./start_slam_simple.sh
```

## 📊 Published Topics

| Topic | Source | Description |
|-------|--------|-------------|
| `/scan` | Scan Restamper | LIDAR scans with synchronised timestamps |
| `/odom_rf2o` | RF2O | LIDAR-based odometry (scan matching) |
| `/odom_motor` | Motor Odom | Motor odometry (dead reckoning) |
| `/odom` | Fusion | **Fused odometry** (used by SLAM) |
| `/map` | SLAM Toolbox | Occupancy map |
| `/map_metadata` | SLAM Toolbox | Map metadata |

## 🔧 Configuration

- **RF2O**: 50Hz, Ceres scan matching
- **Motor Odom**: 50Hz, simple kinematic model
- **Fusion**: RF2O=80%, Motor=20%
- **SLAM**: async, 2.5cm resolution, loop closure 2.0m

## ✅ Status

- ✓ RF2O built and working
- ✓ Motor odometry redirected to `/odom_motor`
- ✓ Fusion node created
- ✓ SLAM reconfigured to use `/odom`
- ✓ The stack starts without errors

## ⚙️ Next steps

1. Test with micro-ROS running (live LIDAR)
2. Check that RF2O receives the scans
3. Validate the fusion of the odometries
4. Test mapping while moving
