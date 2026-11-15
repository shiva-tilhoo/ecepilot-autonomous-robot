# Project milestones

Each folder is a snapshot of the project at one stage, with its original code and documentation. The current version is at the root of the repository (`firmware/`, `ros2/`).

| Folder | What it adds |
|---|---|
| `01_lidar_imu_telemetry/` | First micro-ROS firmware (LD06 LiDAR and MPU6050 published over Wi-Fi) and a C++ ROS 2 workspace: scan buffering, sensor-fusion listener, TF, URDF description of the vehicle, RViz configurations |
| `02_reactive_navigation_firmware/` | "Naive" navigation running on the ESP32: the robot compares the obstacles seen on its left and right and turns towards free space |
| `03_custom_slam_ekf_fusion/` | First complete mapping chain: odometry/IMU fusion with a Kalman filter, frequency analysis and filtering of the IMU, SLAM Toolbox with scan re-stamping |

Inside milestone 03:

- `custom_slam/` holds the two hand-written SLAM implementations that came before SLAM Toolbox (`simple_slam.py`, ICP registration; `slam_v2.py`, filtered scan accumulation);
- `experiments/` gathers the attempts that were later removed: frontier exploration, area coverage, scan accumulation, early firmware variants.

These files had been deleted along the way; they were recovered from the project's git history.

Each firmware expects an `include/secrets.h` file (see `secrets.example.h`).
