# 📐 Diagrams and Visualisation of the Algorithm

## Top view: basic principle

```
                    FRONT (0°)
                       |
                       ▲
        315°--------ROBOT--------45°
        /              |              \
     LEFT          |LIDAR|           RIGHT
      /              |   |              \
  270°             SENSOR             90°
     \              |   |              /
      \             |   |             /
       180° --------+---+--------135°
                    |
                   REAR

ZONES:
  LEFT:  angles 45° to 315° (180 points)
  RIGHT: angles 0-45° + 315-360° (180 points)
```

## Simplified algorithm

```
Fetch the 360 LIDAR points
        │
        ▼
┌─────────────────────┐
│ Count the points    │
│ in each zone:       │
│ - left_count        │
│ - right_count       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Compute balance:    │
│ balance =           │
│ left_count -        │
│ right_count         │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────┐
│ Generate commands:           │
│ throttle = forward_speed     │
│ steering = balance * 255     │
│           / (valid_count+1)  │
└──────────┬───────────────────┘
           │
           ▼
   Send to the motors
        │
        ▼
   🤖 The robot navigates!
```

## Decision diagram: which way to turn?

```
      LIDAR observations
            │
            ▼
    ┌───────────────────────┐
    │ left_count > right    │
    │ count?                │
    │  (More on the left)   │
    └───────┬───────────────┘
            │
    ┌───────┴───────┐
    │ YES      NO   │
    ▼              ▼
┌──────┐      ┌──────┐
│ Turn │      │ Turn │
│ RIGHT│      │ LEFT │
│(away)│      │(away)│
└──────┘      └──────┘
    │              │
    └──────┬───────┘
           │
           ▼
  ┌─────────────────┐
  │ Min distance    │
  │ ahead < 30cm?   │
  └────────┬────────┘
           │
    ┌──────┴──────┐
    │ YES    NO   │
    ▼             ▼
┌──────────┐  ┌─────────┐
│ REVERSE &│  │ GO      │
│ TURN R   │  │ STRAIGHT│
└──────────┘  └─────────┘
```

## Visualisation on a 5x5 grid

### Scenario 1: Free space
```
LIDAR grid seen from above:

    0°  1°  2°  3° ... 358° 359°
LEFT                        RIGHT
  ████████████████████████████
  ████████                ████
  ██                        ██
  ██                        ██
  ████████                ████
  ████████████████████████████

Result: left_count ≈ right_count
        balance ≈ 0
        steering ≈ 0
          
👉 The robot goes straight! ✓
```

### Scenario 2: Wall on the left
```
LIDAR grid:

LEFT                        RIGHT
  ██████████████████████
  ██                    ████
  ██                    ██  ██
  ██                    ██  ██
  ██                    ████
  ██████████████████████████

Result: left_count > right_count
        balance > 0
        steering > 0
          
👉 The robot turns right (towards free space)! ✓
```

### Scenario 3: Obstacle ahead
```
LIDAR grid:

        FRONT (danger!)
           ██████
           ██████
    ████████████████████
    ██              ██
    ██              ██

Result: min_front_dist < DANGER_THRESHOLD
          
👉 The robot reverses and turns right aggressively! ✓
```

## Plot: Balance vs Steering

```
Steering (motor command)
     │
 128 │     ╱
     │    ╱
  64 │   ╱
     │  ╱
   0 ├─────────── balance (left_count - right_count)
     │ ╲
 -64 │  ╲
     │   ╲
-128 │    ╲
     └────────────────
    -200 -100  0  100  200

Interpretation:
- Positive slope: more imbalance = more steering
- Point (0,0): balanced = straight ahead
- Bounds [-128, +128]: saturated = tightest turn
```

## Full architecture

```
┌──────────────────────────────────────────────────────────┐
│                    AUTONOMOUS ROBOT                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐      ┌────────────┐                    │
│  │   LIDAR    │ ───→ │ lidarTask  │                    │
│  │   SERIAL   │      │ (Task 4)   │                    │
│  └────────────┘      └──────┬─────┘                    │
│                             │                           │
│                       ┌─────▼────────┐                 │
│                       │ lidar_buffers│                 │
│                       │  (double-buf)│                 │
│                       └─────┬────────┘                 │
│                             │                           │
│                       ┌─────▼──────────────────────┐   │
│                       │ autonomousTrajectoryTask   │   │
│                       │ (Task 2, 20 Hz)            │   │
│                       │                            │   │
│                       │ 1. Read lidar_buffers      │   │
│                       │ 2. naive_trajectory()      │   │
│                       │ 3. smart_trajectory()      │   │
│                       │ 4. motors_drive()          │   │
│                       └─────┬──────────────────────┘   │
│                             │                           │
│                       ┌─────▼────────────┐             │
│                       │  Motor Drivers   │             │
│                       │  (PWM) L/R       │             │
│                       └─────┬────────────┘             │
│                             │                           │
│  ┌────────────┐      ┌──────▼──────┐                 │
│  │   MOTORS   │ ←─── │ H-bridge    │                 │
│  │   (Left)   │      │ (L298N/etc) │                 │
│  │   (Right)  │      │             │                 │
│  └────────────┘      └─────────────┘                 │
│                                                        │
│  Parallel execution:                                 │
│  ├─ lidarTask (core 1, priority 4)                  │
│  ├─ imuTask (core 1, priority 3)                    │
│  ├─ autonomousTrajectoryTask (core 0, priority 2) ◄─┤ THIS ONE
│  ├─ publishTask (core 0, priority 2)                │
│  └─ loop (core 1)                                    │
│                                                        │
└──────────────────────────────────────────────────────────┘
```

## Timing diagram

```
Time
 ▲
 │
 │ autonomousTrajectoryTask (20 Hz, 50ms)
 │
100ms├─────────────────────────────────────────────────
     │ Iteration 1  │  Iter 2  │  Iter 3  │  Iter 4
 50ms├──┬─────────────┬────────┬─────────┬────────────
     │  │             │        │         │
  0ms└──┴─────────────┴────────┴─────────┴────────────
        │ Processing │ Waiting │ PWM     │
        │   (< 1ms)  │ (49ms)  │  sent   │
        │            │         │         │
        │Compute     │Wait     │Apply    │
        │lidar       │FreeRTOS │motors   │
```

## Robot states: state machine

```
┌──────────────┐
│  ROBOT STOP  │◄─────────┐
│ (motors=0)   │           │ autonomous_mode = false
└───────┬──────┘           │
        │                  │
        │ autonomous_mode = true
        ▼
┌──────────────────────────┐
│  AUTONOMOUS ROBOT        │
│ (navigating)             │
├──────────────────────────┤
│ • Reads the LIDAR        │◄───┐
│ • Computes the direction │    │
│ • Sends PWM to the motors│    │
│ • Forward/Turn/Reverse   │    │
└───────┬──────────────────┘    │
        │                       │
        └───────── Loop ────────┘
              (every 50ms)
```

## Heatmap: distribution of the decisions

```
Example: exploring an L-shaped space

ZONE 1 (Vertical)   ZONE 2 (Horizontal)
Goes straight       ▲ Turns right
        │           │
════════╋═══════════●═════════════
        │           │
Free space          Free space

Robot trace:
●───────────┐
│           │
│  ●──●     │  The LIDAR detects the bend
│  │  │     │  and the robot turns naturally!
│  └──┘     │
│        ●  │
│        │  │
│        └──┘
```

## Comparison: Naive vs Smart

```
Scenario: close obstacle ahead

       NAIVE:                    SMART:
    ┌─────────┐               ┌─────────┐
    │ Forward │               │ Detects │
    │ Reverse │ ─→ Collision  │ distance│
    │ Turn    │               └────┬────┘
    └─────────┘                    │
                                   ▼
                            ┌──────────────┐
                            │ min_dist<30cm│
                            │ Reverse+Turn │
                            │ Avoided! ✓   │
                            └──────────────┘
```
