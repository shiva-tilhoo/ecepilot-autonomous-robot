# Naive Trajectory Algorithm

## Overview

This algorithm drives the robot by analysing the distribution of the points detected by the lidar. The principle is simple and intuitive:

- **More points on the left → the robot turns right**
- **More points on the right → the robot turns left**

This lets the robot avoid obstacles naturally by heading towards free space.

## How it works

### 1. `naive_trajectory()` function

This is the core of the algorithm. It splits the lidar field into two zones:

**Left zone**: angles 45° to 315° (left half of the robot)
**Right zone**: angles 315° to 45° (right half of the robot)

```
        0° (FRONT)
        |
  315°--+--45°
  /     |     \
270°    |      90°
  \     |     /
  225° ROBOT 135°
       (TOP VIEW)

Left: angles 45-315°
Right: angles 315-360° + 0-45°
```

#### Algorithm:

1. **Count the points**: 
   - `left_count`: number of points detected on the left
   - `right_count`: number of points detected on the right
   - Only points between 0 and `max_range` are counted

2. **Compute the balance**:
   ```
   balance = left_count - right_count
   ```

3. **Motor commands**:
   - **Throttle (forward/backward)**: constant forward speed
   - **Steering (direction)**: proportional to the imbalance
     - If `balance > 0` (more on the left) → positive steering (turn right)
     - If `balance < 0` (more on the right) → negative steering (turn left)
     - If `balance ≈ 0` (balanced) → steering ≈ 0 (go straight)

### 2. `smart_trajectory()` function (improved version)

Extension of the naive algorithm with close-obstacle detection:

- Detects obstacles **in front of the robot** (angles 330-30°)
- If an obstacle is detected closer than `danger_threshold` (30 cm by default):
  - **Reverses** immediately
  - **Turns right** aggressively
- Otherwise it uses the normal naive algorithm

## Usage

### Enabling autonomous mode

In the code or through a control interface:

```cpp
// Enable autonomous mode
autonomous_mode = true;
autonomous_throttle = 150;  // Forward speed (0-255)

// Later: disable
autonomous_mode = false;
motors_stop();  // Stop the robot
```

### `autonomousTrajectoryTask` task

This FreeRTOS task:
- Runs at **20 Hz** (every 50ms)
- Fetches the lidar data
- Computes the trajectory command
- Sends the commands to the motors through `motors_drive()`

## Configurable parameters

In the `autonomousTrajectoryTask()` function:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `MAX_RANGE` | 300.0f cm | Maximum lidar distance taken into account |
| `DANGER_THRESHOLD` | 30.0f cm | Minimum distance to an obstacle (automatic reverse) |
| `BASE_THROTTLE` | 150 | Forward speed (0-255) |

## Limitations and possible improvements

### Current limitations:
1. **No memory**: each decision is made independently
2. **No optimisation**: no long-term trajectory planning
3. **Sensitive to noise**: false lidar points can affect the direction
4. **Possible oscillations**: when the obstacles are symmetric

### Future improvements:
1. **Temporal filtering**: moving average of the last decisions
2. **Priority zones**: give more weight to close points
3. **Dead-end detection**: recognise blocked situations
4. **Spatial memory**: remember the paths already explored
5. **Progressive acceleration**: adapt the speed to the obstacles

## Example: getting out of a maze

With this algorithm:
1. The robot goes straight when the space is free
2. When it approaches a wall:
   - One of the sides sees more points
   - It naturally turns to the other side
3. No complex logic is needed, only the physics of free space!

## Integration with ROS 2

- The lidar publishes its data on `/scan` (ROS2 topic)
- The autonomous task reads the internal buffers directly
- No ROS latency - real-time processing
- Motor commands are applied directly

## Control structure

```
┌─────────────────┐
│  Lidar SERIAL   │
└────────┬────────┘
         │ (raw data)
         ▼
┌─────────────────┐
│  lidarTask      │ (Task 4, core 1)
└────────┬────────┘
         │ (updates lidar_buffers)
         ▼
┌─────────────────────────────────────┐
│  autonomousTrajectoryTask           │ (Task 2, core 0)
│  • Reads lidar_buffers              │
│  • Computes naive_trajectory()      │
│  • Calls motors_drive()             │
└────────┬────────────────────────────┘
         │ (PWM commands)
         ▼
┌─────────────────┐
│  Motor drivers  │
└─────────────────┘
```

## Debugging

The autonomous task prints every second:
```
[TRAJ] throttle=150 steering=32 | left=45 right=38 total=83
```

- `throttle`: forward speed currently applied
- `steering`: steering angle (-128 to +128)
- `left`: number of points detected on the left
- `right`: number of points detected on the right
- `total`: total number of valid points

## Example scenarios

### Situation 1: Straight corridor
```
LIDAR top view:

LEFT  │  FRONT  │  RIGHT
█████ │  ▓▓▓▓▓  │ █████
█████ │  ▓▓▓▓▓  │ █████

Result: left_count ≈ right_count → steering ≈ 0 → goes straight ✓
```

### Situation 2: Wall on the left
```
LEFT  │  FRONT  │  RIGHT
██ ▓▓ │  ▓▓▓▓▓  │ █████
██ ▓▓ │  ▓▓▓▓▓  │ █████

Result: left_count > right_count → steering > 0 → turns right ✓
```

### Situation 3: Obstacle ahead
```
LEFT  │  FRONT  │  RIGHT
█████ │  ███░░░ │ █████
█████ │  ███░░░ │ █████

Result: min_front_dist < danger_threshold → reverses and turns ✓
```
