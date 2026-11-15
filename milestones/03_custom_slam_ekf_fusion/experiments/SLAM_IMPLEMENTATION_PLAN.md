# SLAM Implementation Plan - Based on the ECE SLAM Lecture

## 📋 Project Goals
1. **Localization**: absolute position of the robot (x, y, θ) in its map
2. **Mapping**: build a probabilistic occupancy grid 
3. **Simultaneous**: with no initial assumptions, localise while building the map
4. **Planning**: navigate in the incomplete map

---

## 🏗️ Overall Architecture (after Nav2)

```
ESP32 (Sensors) 
    ↓ MicroROS
ROS2 Topics (/scan, /imu/data)
    ↓
┌─────────────────────────────────┐
│  SLAM Toolbox (simple_slam.py)  │ ← Localization + Mapping
│  - ICP scan matching            │
│  - Occupancy grid update        │
│  - Transform /map → /base_link  │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  Nav2 Framework                 │ ← Planning + Control
│  - Planner Server (path)        │
│  - Controller Server (velocity) │
│  - BT Navigator                 │
└─────────────────────────────────┘
    ↓
Motor Commands (PWM) → ESP32
```

---

## 📍 Phase 1: Localization (Sensor Fusion)

### 1.1 Available Sensors
- **LD06 LIDAR**: 30 Hz, 360 points/scan, distance + intensity
- **MPU6050 IMU**: accelerometer (100Hz raw), gyro (100Hz raw), magnetometer
- **No encoder**: ❌ no direct odometry

### 1.2 Fusion Strategy (Kalman Filter)

**State model** (simplified 2D):
```
State = [x, y, θ, vx, vy, ωz]

Propagation (IMU @ 100Hz):
  x(k+1) = x(k) + vx(k)·Δt + 0.5·ax·Δt²
  y(k+1) = y(k) + vy(k)·Δt + 0.5·ay·Δt²
  θ(k+1) = θ(k) + ωz(k)·Δt
  
  vx(k+1) = vx(k) + ax·Δt
  vy(k+1) = vy(k) + ay·Δt
  ωz(k+1) = ωz(k) + αz·Δt
```

**Available measurements**:
- **LIDAR** (30 Hz): relative position through ICP matching
  - Input: two consecutive scans
  - Output: Δx, Δy, Δθ (rigid transform)
  
- **IMU** (100 Hz): acceleration + angular velocity
  - EMA filter already implemented (alpha=0.35/0.4)

**Fusion process**:
```python
# Kalman Filter pseudo-code
def kalman_update(state, P, imu_accel, imu_gyro, lidar_delta_pose):
    # Prediction (IMU)
    state_pred = propagate_imu(state, imu_accel, imu_gyro, dt=0.01)
    P_pred = F @ P @ F.T + Q_imu  # Q_imu = IMU covariance
    
    # LIDAR correction (every 3-4 IMU samples)
    if lidar_measurement_available:
        innovation = lidar_delta_pose - H @ state_pred
        S = H @ P_pred @ H.T + R_lidar  # R_lidar = LIDAR covariance
        K = P_pred @ H.T @ inv(S)
        state = state_pred + K @ innovation
        P = (I - K @ H) @ P_pred
    else:
        state = state_pred
        P = P_pred
    
    return state, P, covariance
```

### 1.3 Implementation in simple_slam.py

**IMULocalization class**:
```python
class KalmanFilter2D:
    def __init__(self):
        self.state = np.array([0, 0, 0, 0, 0, 0])  # x,y,θ,vx,vy,ωz
        self.P = np.eye(6) * 0.1  # Initial covariance
        self.Q = np.eye(6) * [0.001, 0.001, 0.0001, 0.01, 0.01, 0.01]  # IMU noise
        self.R = np.eye(3) * [0.01, 0.01, 0.005]  # LIDAR noise (ICP)
    
    def predict(self, ax, ay, gz, dt):
        # Velocity update
        vx_new = self.state[3] + ax * dt
        vy_new = self.state[4] + ay * dt
        
        # Position update
        x_new = self.state[0] + self.state[3] * dt + 0.5 * ax * dt**2
        y_new = self.state[1] + self.state[4] * dt + 0.5 * ay * dt**2
        θ_new = self.state[2] + self.state[5] * dt
        
        self.state = np.array([x_new, y_new, θ_new, vx_new, vy_new, gz])
        self.P = self.F @ self.P @ self.F.T + self.Q
    
    def update_lidar(self, delta_x, delta_y, delta_theta):
        # LIDAR correction
        innovation = np.array([delta_x - self.state[0],
                               delta_y - self.state[1],
                               delta_theta - self.state[2]])
        
        K = self.P[:3, :3] @ inv(self.P[:3, :3] + self.R)
        self.state[:3] += (K @ innovation)
        self.P -= K @ self.P[:3, :3]
```

### 1.4 Expected Results
- ✅ Position (x, y, θ) updated in real time
- ✅ Uncertainty (covariance) estimated
- ✅ Published on `/odometry/filtered`

---

## 🗺️ Phase 2: Mapping (Occupancy Grid)

### 2.1 Map Representation

**Probability grid**:
```
Grid = 2D array, 50m × 50m, 10cm resolution = 500×500 cells

Cell[x, y] ∈ [0, 1]
  0.0 = Free
  0.5 = Unknown (prior)
  1.0 = Occupied
```

**Memory footprint**:
```
500 × 500 cells × float32 = 1 MB ✓ Acceptable
```

### 2.2 LIDAR Sensor Model

**Ray casting** (for each LIDAR point):
```python
# Bresenham line from robot position to hit point
ray = bresenham_line(robot_pos, hit_point)

for cell in ray[:-1]:
    # Cells crossed = free
    p_free = 0.25  # Prior: 25% occupied
    update_cell(cell, p_free)

for cell in [hit_point]:
    # Last cell = occupied
    p_occupied = 0.75  # Prior: 75% occupied
    update_cell(cell, p_occupied)
```

### 2.3 Bayesian Update

**Bayes' formula** (as in the lecture handout):
```
P(m_i | z_{1:t}) = P(z_t | m_i) · P(m_i | z_{1:t-1}) / P(z_t)

Implemented in log-odds (numerically stable):
```

```python
def update_occupancy_grid(grid, robot_pose, lidar_scan):
    for angle, distance in lidar_scan.points:
        if distance > MAX_RANGE:
            continue
        
        # Absolute angle
        world_angle = robot_pose.theta + angle
        hit_x = robot_pose.x + distance * cos(world_angle)
        hit_y = robot_pose.y + distance * sin(world_angle)
        
        # Ray from the robot to the hit
        ray = bresenham_line(robot_pose.xy, (hit_x, hit_y))
        
        for cell in ray[:-1]:
            # Free
            grid[cell] = occupancy_update(grid[cell], p_hit=0.2)
        
        # Occupied
        grid[ray[-1]] = occupancy_update(grid[ray[-1]], p_hit=0.8)

def occupancy_update(p_prior, p_hit):
    # Bayes rule in log-odds
    log_odds = log(p_prior / (1 - p_prior)) + log(p_hit / (1 - p_hit))
    p_post = 1 - 1 / (1 + exp(log_odds))
    return p_post
```

### 2.4 ROS2 Publishing

```python
# Topic: /map (OccupancyGrid)
map_msg = OccupancyGrid()
map_msg.header.frame_id = "map"
map_msg.info.resolution = 0.1  # 10cm
map_msg.info.width = 500
map_msg.info.height = 500
map_msg.info.origin.position.x = -25  # Centred
map_msg.info.origin.position.y = -25

# Convert [0,1] → [0,100] for OccupancyGrid
map_msg.data = (grid * 100).flatten().astype(int8)
```

### 2.5 Expected Results
- ✅ Map visible in RViz (free/occupied space)
- ✅ Real-time update (~10-20 FPS)
- ✅ Memory < 10 MB

---

## 🚀 Phase 3: Autonomous Navigation (Mapping Circuit)

### 3.1 Coverage Strategy

As mentioned in the handout, there are several approaches:

**Option 1: Random Walk** (currently implemented)
```
✓ Guarantees complete coverage
✗ Inefficient, very slow
```

**Option 2: Spiral Coverage** (recommended)
```cpp
// Pseudo-code
void spiral_mapping() {
    float radius = 0.5;  // 50cm at first
    
    while (radius < MAX_RADIUS) {
        // Drive in a spiral
        for (int i = 0; i < 8; i++) {
            angle = i * 45°;
            move_forward(radius);
            turn(45°);
        }
        radius += 1.0;  // Increase the radius
    }
}
```

**Option 3: Wall Following**
```
Follow the left wall → coverage of the boundaries
```

### 3.2 Adapting the Existing main.cpp

**Current state**:
```cpp
enum MappingState { IDLE, MOVING_FORWARD, TURNING, COMPLETING_CIRCUIT };

// Simple circuit: 4×4m square, ~18 seconds
// forward 3s, turn 0.5s × 4 = full circuit
```

**Improvement towards a spiral**:
```cpp
void motors_drive_spiral() {
    static float radius = 0.5;
    static int spiral_count = 0;
    
    if (spiral_count < 8) {
        motors_drive(200, 0);  // Forward
        spiral_count++;
    } else {
        motors_drive(0, 100);  // Turn
        radius += 0.2;
        spiral_count = 0;
    }
}
```

### 3.3 Loop Closure Detection

**Problem**: after completing a circuit, the robot is at (0,0) but SLAM believes it is somewhere else → **drift**.

**Solution: Improved Scan Matching (ICP)**
```python
def detect_loop_closure(current_scan, reference_scans):
    """
    Compare the current scan with the older scans
    If the match is above the threshold: loop closed!
    """
    for ref_scan in reference_scans[-20:]:  # Last 20 scans
        icp_error, transform = icp_align(current_scan, ref_scan)
        
        if icp_error < THRESHOLD:  # e.g. < 0.1m
            # Loop closure detected!
            graph.add_constraint(current_pose, ref_pose, transform)
            optimize_graph()  # Correct the whole path
            return True
    
    return False
```

---

## 🎯 Phase 4: Navigation (Nav2 Integration)

### 4.1 Architecture

```
Simple SLAM (already available ✓)
    ↓ /map, /odometry
Nav2 Framework
    ├─ Planner (Dijkstra, A*, RRT)
    ├─ Controller (DWA, PurePersuit)
    └─ BT Navigator (behavior tree)
    ↓ /cmd_vel
Motor Controller (in main.cpp)
```

### 4.2 Installing Nav2

```bash
sudo apt install ros-humble-nav2*
sudo apt install ros-humble-slam-toolbox
```

### 4.3 Configuration (Nav2)

**`nav2_config.yaml` file**:
```yaml
planner_server:
  plugins: ["GridBased"]
  GridBased:
    plugin: "nav2_theta_star_planner/ThetaStarPlanner"  # or Dijkstra
    
controller_server:
  plugins: ["FollowPath"]
  FollowPath:
    plugin: "nav2_pure_pursuit_controller/PurePursuitController"
    desired_linear_vel: 0.5
    max_angular_vel: 2.0
```

### 4.4 ROS2 Node for the Motors

```python
class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.motor_pub = self.create_publisher(Int16MultiArray, '/motors', 10)
    
    def cmd_vel_callback(self, msg):
        """
        Twist msg (vx, ωz) → PWM commands
        Convert velocities into PWM for the motors
        """
        # v = 0.5 m/s → throttle = 200 PWM
        throttle = int(msg.linear.x / 0.5 * 200)
        
        # ω = 1.0 rad/s → steering = 100 PWM (radius = ~0.5m)
        steering = int(msg.angular.z / 1.0 * 100)
        
        self.motor_pub.publish(
            Int16MultiArray(data=[throttle, steering])
        )
```

---

## 📊 Summary of the Implementation Steps

| Phase | Component | Priority | Effort | State |
|-------|-----------|----------|--------|-------|
| 1 | Kalman Filter (IMU + LIDAR) | 🔴 Critical | 40h | ⏳ To do |
| 2 | Occupancy Grid Mapping | 🟠 High | 30h | ⏳ Partial |
| 3 | Loop Closure Detection | 🟡 Medium | 20h | ❌ Missing |
| 4 | Spiral Coverage | 🟡 Medium | 10h | ❌ Missing |
| 5 | Nav2 Integration | 🟢 Low | 25h | ❌ Missing |

---

## 🔧 Files to Create/Modify

### To create:
1. **`localization_node.py`** - Kalman Filter for sensor fusion
2. **`mapping_node.py`** - Occupancy grid update (improves simple_slam.py)
3. **`loop_closure_node.py`** - Loop detection
4. **`nav2_config.yaml`** - Nav2 configuration

### To modify:
1. **`main.cpp`** - Add the spiral instead of the simple circuit
2. **`simple_slam.py`** - Add the Kalman Filter
3. **`start_stack.sh`** - Add the new nodes

---

## 🎓 Handout References

- **Kalman Filtering**: slides 14-15 (sensor fusion)
- **Bayesian Mapping**: slides 22-24 (occupancy grid)
- **Coverage Strategies**: slides 28-29 (spiral, wall-following)
- **Planning While Mapping**: slides 32-40 (trajectory computation)
- **Nav2 Framework**: slides 47-50 (overall architecture)

---

## 📝 Validation Checklist

- [ ] The Kalman Filter builds and publishes /odometry/filtered
- [ ] The occupancy grid is visible in RViz
- [ ] Spiral mapping covers the whole area
- [ ] Loop closure detects the return to the start point
- [ ] Loop closure error < 0.5m
- [ ] Nav2 generates valid trajectories
- [ ] The robot follows the /cmd_vel commands from Nav2

---

## 🚀 Immediate Next Steps

1. **This week**: implement the Kalman Filter in simple_slam.py
2. **Week 2**: test mapping with spiral coverage
3. **Week 3**: integrate loop closure detection
4. **Week 4**: install and configure Nav2
5. **Week 5**: full integration tests
