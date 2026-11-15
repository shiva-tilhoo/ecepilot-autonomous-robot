# 🚀 Quick Start - Naive Trajectory Algorithm

## TL;DR

An **autonomous navigation algorithm** that drives the robot from the LIDAR data alone.

## ⚡ 5 minutes to get started

### 1. Check the structure
```
02_reactive_navigation_firmware/
├── src/main.cpp        ← Main code
├── src/motors.cpp      ← Motor implementation
├── include/motors.h    ← Motor control
└── docs/
    ├── ALGORITHM.md
    ├── DIAGRAMS.md
    └── SUMMARY.md
```

### 2. Enable autonomous mode

**Option A: Simple** (in `setup()` or a function)
```cpp
void start_autonomous() {
  autonomous_mode = true;
  // The robot navigates by itself!
}
```

**Option B: With speed control**
```cpp
void start_with_speed(int speed) {
  autonomous_throttle = speed;    // 0-255
  autonomous_mode = true;
}
```

### 3. Stop
```cpp
void stop_autonomous() {
  autonomous_mode = false;
  motors_stop();
}
```

## 📊 How it works in 30 seconds

```
┌─────────────────┐
│   LIDAR (360°)  │
└────────┬────────┘
         │
  Counts the obstacles:
   Left (45-315°)  vs  Right (0-45°, 315-360°)
         │
   More on the left?  → Turn right
   More on the right? → Turn left
   Balanced?          → Go straight
         │
  ┌─────┴─────┐
  │  Motors   │
  └───────────┘
      ↓
   🤖 THE ROBOT NAVIGATES!
```

## 🎮 Control through Serial (optional)

Add this to `loop()`:

```cpp
void loop() {
  if(Serial.available()) {
    char cmd = Serial.read();
    if(cmd == 'a') autonomous_mode = true;
    if(cmd == 's') { autonomous_mode = false; motors_stop(); }
    if(cmd == '+') autonomous_throttle += 10;
    if(cmd == '-') autonomous_throttle -= 10;
  }
}
```

Then in the Serial Monitor:
- `a` = Autonomy ON
- `s` = Stop
- `+` = Faster
- `-` = Slower

## 📈 Watching the algorithm

Every second, the firmware prints:
```
[TRAJ] throttle=150 steering=32 | left=45 right=38 total=83
       └──────┬──────┘ └─────┬─────┘ └──────────┬──────────┘
          Motors     Direction   Lidar points detected
```

This shows:
- **throttle**: forward speed (-255 to +255)
- **steering**: direction (-128 to +128) - positive = right
- **left/right/total**: number of points in each zone

## 🔧 Parameters to adjust

In `main.cpp`, function `autonomousTrajectoryTask()`:

```cpp
const float MAX_RANGE = 300.0f;        // ← Max LIDAR distance
const float DANGER_THRESHOLD = 30.0f;  // ← Min distance before reversing
const int BASE_THROTTLE = 150;         // ← Base speed
```

### When to adjust them:

| Problem | Solution |
|---------|----------|
| The robot oscillates | Lower `BASE_THROTTLE` |
| Does not see obstacles | Increase `MAX_RANGE` |
| Too aggressive | Reduce `MAX_RANGE` |
| Reverses too easily | Increase `DANGER_THRESHOLD` |
| Too slow | Increase `BASE_THROTTLE` |

## 🧪 Quick tests

### Test 1: Open space
```cpp
autonomous_throttle = 150;
autonomous_mode = true;
delay(5000);
autonomous_mode = false;
// → The robot should go straight
```

### Test 2: With an obstacle
```cpp
// Put a hand/obstacle in front of the LIDAR
autonomous_mode = true;
// → The robot should reverse and turn
autonomous_mode = false;
```

### Test 3: Short navigation
```cpp
autonomous_mode = true;
delay(30000);  // 30 seconds
autonomous_mode = false;
// → Watch how it navigates/avoids obstacles
```

## 🎯 What the algorithm does well

✅ Avoids obstacles automatically
✅ Heads towards free space
✅ Runs in real time (20 Hz)
✅ No complex configuration
✅ Robust to missing LIDAR data

## ⚠️ What the algorithm does not do

❌ Optimise the trajectory (shortest path)
❌ Remember visited places
❌ Detect specific objects
❌ Build a map

## 📚 More information

- **ALGORITHM.md** - Full technical explanation
- **DIAGRAMS.md** - Diagrams and visualisations
- **README.md** (parent folder) - Detailed overview

## ✅ Checklist before running

- [ ] Motors initialised (`motors_init()` in setup)
- [ ] LIDAR connected and publishing data
- [ ] Autonomous task created (`autonomousTrajectoryTask`)
- [ ] Serial Monitor at 115200 baud
- [ ] Test area free of obstacles

## 🚀 Start in 3 lines

```cpp
// In setup():
motors_init();
autonomous_mode = true;

// ✓ That's all! The robot is now navigating.
```

## 🆘 Quick troubleshooting

| Symptom | Solution |
|---------|----------|
| Nothing happens | Check `autonomous_mode = true` |
| The robot spins in place | Is the LIDAR detecting an obstacle? |
| Build errors | Check `#include "motors.h"` |
| Serial shows nothing | Check the 115200 baud rate |
| Motors do not turn | Check the motor pins in the configuration |

## 💡 Tips

- Start with `BASE_THROTTLE = 100` (slow and safe)
- Increase gradually, up to 200 at most
- Test in an open space first (car park, garage)
- Watch the Serial logs to debug
- Symmetric obstacles can cause oscillation

## 🎓 Topics covered

✓ Real-time processing of LIDAR data
✓ Autonomous navigation algorithms
✓ Multi-task FreeRTOS programming
✓ Motor control from sensor feedback
✓ Robotics debugging
