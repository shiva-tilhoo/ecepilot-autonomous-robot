# ROS 2 stack

Python nodes, launchers and configurations that run on the PC (ROS 2 Humble). The launchers change into this folder by themselves, so they can be called from anywhere.

## Launchers

| Script | Purpose |
|---|---|
| `start_auto_slam_only.sh` | Full simulation: 2D simulator, ROS 2 bridge, SLAM Toolbox, map export |
| `start_robot_mapping_auto.sh` | Real robot: LiDAR TF, scan re-stamping, SLAM in pure scan-matching mode, wall centering |

## Nodes

| File | Role |
|---|---|
| `scan_restamper_simple.py` | Republishes `/scan_raw` on `/scan` with the PC clock (the ESP32 is not time-synchronised) |
| `motor_odom_simple.py` | Publishes `/odom` and the `odom → base_link` TF with a very high covariance |
| `wall_centering_node.py` | Autonomous driving: keeps the robot in the middle of the corridor from the scan |
| `trajectory_saver.py` | Records the actual robot trajectory from the points provided by the end-of-lap detector |
| `slam_initial_pose_setter.py`, `slam_odom_from_tf.py`, `slam_map_saver.py` | Helpers around SLAM Toolbox: initial pose, odometry derived from TF, PNG export of the map |
| `odom_to_tf.py`, `wait_for_topic.py` | Start-up utilities |
| `teleop_keyboard.py` | Keyboard teleoperation |
| `compare_rf2o_vs_slam.py` | Comparison of RF2O, SLAM and ground-truth odometry |

## Simulator

| File | Role |
|---|---|
| `simu_lidar_auto.py` | pygame simulator: simulated robot and LiDAR, autonomous mode, return to start (recorded path, A\*, Nav2) |
| `simu_bridge.py` | Bridge between the simulator and the ROS 2 topics (`/scan`, ground-truth odometry) |
| `simu2d_*.py` | First version of the simulator, connected to ROS 2 through a socket |
| `image_corridor_widened.png` | Track used by the simulator (prepared with `track_images/`) |

## Sub-folders

- `config/`: SLAM Toolbox parameters (one file per scenario), RF2O and Nav2.
- `tools/`: motion tests, LiDAR diagnostics, RF2O launchers, and the experimental sequence mapping → end-of-lap detection → return (`real_robot_mapping_auto.sh`).
- `legacy/`: previous versions of the nodes (EKF, lifecycle nodes, naive algorithms v1 to v4).
- `track_images/`: Pillow scripts that turn a track picture into a map usable by the simulator.

## Dependencies

```bash
sudo apt install ros-humble-slam-toolbox ros-humble-tf2-ros ros-humble-navigation2
pip install -r requirements.txt
```

`rf2o_laser_odometry` is built from source in the colcon workspace.
