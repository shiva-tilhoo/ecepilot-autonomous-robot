# Naive Trajectory Algorithm - Overview

## 🤖 Description

Implementation of a **naive autonomous navigation algorithm** for a mobile robot, based on **LIDAR** data.

**Key idea**: the algorithm counts the obstacles on the left and on the right, then turns towards the freer side.

```
More obstacles on the left   → Turn right
More obstacles on the right  → Turn left
Balanced                     → Go straight
```

## 📋 Files

| File | Description |
|------|-------------|
| `src/main.cpp` | Main code with the implementation of the algorithm |
| `include/motors.h` | Motor control header |
| `src/motors.cpp` | Motor control implementation |
| `docs/ALGORITHM.md` | Detailed documentation of the algorithm |
| `README.md` | This file |

## ⚙️ Main components

### 1. **Data structures**

```cpp
// Trajectory command (output of the algorithm)
typedef struct {
  int throttle;   // Forward/backward speed (-255 to +255)
  int steering;   // Direction (-255 to +255)
} TrajectoryCommand;
```

### 2. **Naive function: `naive_trajectory()`**

Basic implementation of the idea:

```cpp
TrajectoryCommand naive_trajectory(float ranges[], float max_range, int forward_speed)
```

**Parameters:**
- `ranges[]`: array of lidar distances (360 points)
- `max_range`: maximum distance in cm (300 by default)
- `forward_speed`: desired forward speed (0-255)

**Returns:**
- A `TrajectoryCommand` structure with throttle and steering

**How it works:**
1. Splits the lidar into two zones (left/right)
2. Counts the valid points in each zone
3. Computes the imbalance (balance)
4. Converts it into motor commands

### 3. **Smart function: `smart_trajectory()`**

Improved version with close-obstacle detection:

```cpp
TrajectoryCommand smart_trajectory(float ranges[], float max_range, 
                                   int forward_speed, float danger_threshold)
```

**Improvements:**
- Detects frontal obstacles
- Reverses automatically when too close
- Otherwise uses the naive algorithm

### 4. **FreeRTOS task: `autonomousTrajectoryTask()`**

Infinite loop that:
- Runs at 20 Hz (every 50ms)
- Fetches the lidar data
- Calls `smart_trajectory()`
- Sends the commands to the motors

## 🚀 Usage

### Simple activation

```cpp
// In setup() or loop()
autonomous_mode = true;  // Enable autonomy
autonomous_throttle = 150;  // Speed (0-255)

// Later
autonomous_mode = false;  // Stop
motors_stop();
```

### From the Serial console

```
'a' - Autonomy ON
's' - Stop (OFF)
'+' - Increase speed
'-' - Decrease speed
```

## 📊 Monitoring/Debugging

Every second, the task prints:

```
[TRAJ] throttle=150 steering=32 | left=45 right=38 total=83
```

- **throttle**: current forward speed (-255 to +255)
- **steering**: steering angle (-128 to +128)
- **left**: obstacle points on the left
- **right**: obstacle points on the right
- **total**: valid points detected

## 🔧 Configurable parameters

In `autonomousTrajectoryTask()`:

```cpp
const float MAX_RANGE = 300.0f;        // Max LIDAR distance (cm)
const float DANGER_THRESHOLD = 30.0f;  // Safety distance (cm)
const int BASE_THROTTLE = 150;         // Forward speed (0-255)
```

## 📈 Execution diagram

```
setup()
├─ motors_init()              ← Initialise the motors
├─ lidarTask (Task 4)         ← Read the LIDAR
├─ imuTask (Task 3)           ← Read the IMU
├─ autonomousTrajectoryTask (Task 2) ← ALGORITHM ← HERE!
└─ publishTask (Task 2)       ← Publish on ROS2

autonomousTrajectoryTask (20 Hz)
├─ if autonomous_mode == true
├─ Fetch lidar_buffers
├─ Call smart_trajectory()
├─ Call motors_drive()
└─ Wait 50ms
```

## ✅ Strengths of the implementation

| Strength | Description |
|----------|-------------|
| **Real time** | No ROS overhead, direct processing |
| **Parallel** | Independent FreeRTOS task |
| **Simple** | ~100 lines of code |
| **Robust** | Handles missing lidar data |
| **Configurable** | Several adjustable parameters |
| **Debuggable** | Detailed logs every second |

## ⚠️ Limitations

| Limitation | Impact |
|-----------|--------|
| No memory | Each decision is independent |
| No planning | No optimised path |
| Sensitive to noise | False lidar points → wrong direction |
| May oscillate | In symmetric spaces |
| No anti-deadlock | Can get stuck in a dead end |

## 🔮 Possible future improvements

1. **Temporal filtering**: moving average of the commands
2. **Distance weighting**: give more weight to close points
3. **Dead-end detection**: if there are no points → exit spiral
4. **Spatial memory**: remember the explored areas
5. **Wall-following mode**: follow the walls
6. **Machine Learning**: learn the best parameters

## 📝 Basic code example

```cpp
// In loop() or a function
void main_autonomous_example() {
  // Enable
  autonomous_mode = true;
  
  // Watch the navigation for 30 seconds
  // The Serial logs show:
  // [TRAJ] throttle=150 steering=32 | left=45 right=38 total=83
  
  delay(30000);
  
  // Stop
  autonomous_mode = false;
  motors_stop();
}
```

## 🔗 Dependencies

- `Arduino.h` - Arduino framework
- `motors.h` - Motor control
- `FreeRTOS` - Parallel tasks
- LIDAR data through `lidar_buffers`

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| The robot does not move | Check `autonomous_mode = true` |
| Turns in circles | Increase `MAX_RANGE` or lower the speed |
| Jerky motion | Reduce `BASE_THROTTLE` |
| Does not see obstacles | Check the LIDAR in the Serial monitor |
| Missing logs | Check that Serial runs at 115200 baud |

## 📊 Comparison: Naive vs Smart

| Aspect | Naive | Smart |
|--------|-------|-------|
| Complexity | Low | Low+ |
| Far obstacle detection | Yes | Yes |
| Close obstacle detection | Yes | Yes + automatic reverse |
| Computation time | ~1ms | ~2ms |
| Recommended for | Open spaces | Everywhere |

## 🎯 Use cases

✅ **Good for:**
- Simple exploration
- Basic obstacle avoidance
- Fast prototyping
- Learning (understanding how it works)

❌ **Not ideal for:**
- Precise/optimised navigation
- Very cluttered spaces
- Trajectories defined in advance
- Critical production use

## 📚 Further reading

- See `docs/ALGORITHM.md` for the technical details
- Read the comments in `src/main.cpp`

---

**Built for the 4th-year technical project**
**Date: February 2026**
