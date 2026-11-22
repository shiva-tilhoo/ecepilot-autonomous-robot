#!/usr/bin/env python3
import pygame, math, socket, pickle, struct, os, time, threading, heapq
import numpy as np

try:
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from geometry_msgs.msg import PoseStamped
    from geometry_msgs.msg import Twist
    from geometry_msgs.msg import TransformStamped
    from tf2_msgs.msg import TFMessage
    from tf2_ros import TransformBroadcaster
    from nav2_msgs.action import NavigateToPose, NavigateThroughPoses
    from nav_msgs.msg import OccupancyGrid, Path
    from std_srvs.srv import Empty
    ROS2_AVAILABLE = True
except Exception:
    ROS2_AVAILABLE = False

# --- CONFIG ---
WIDTH, HEIGHT = 800, 600
MAP_RES       = 0.0133
NUM_RAYS      = 180
CIRCUIT_PATH  = "image_corridor_widened.png"

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 16, bold=True)

if os.path.exists(CIRCUIT_PATH):
    circuit_surf = pygame.image.load(CIRCUIT_PATH).convert()
    circuit_surf = pygame.transform.scale(circuit_surf, (WIDTH, HEIGHT))
else:
    circuit_surf = pygame.Surface((WIDTH, HEIGHT))
    circuit_surf.fill((255,255,255))

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('127.0.0.1', 5005))
server_sock.listen(1)
server_sock.setblocking(False)

robot_pos, robot_th = [150.0, 250.0], 0.0
start_pos = [150.0, 250.0]  # 🎯 START POINT - for visual comparison
lidar_conn = None

# --- AUTONOMY PARAMETERS (SAME AS wall_centering_node) ---
CRUISE_SPEED = 0.7        # 🐢 Reduced speed for better RF2O accuracy
ALPHA_ROT = 0.95          # Very strong damping (as in wall_centering)
DEADZONE = 0.15           # LARGER dead zone (metres) - stays centred without oscillating
GAIN_ROT = 0.4            # Very gentle gain to "glide" through the turns
MIN_ROTATION = 0.38       # Minimum threshold that makes the motors move
MAX_LINEAR_SPEED = 0.7    # Global linear speed cap (px/frame)
MAX_ANGULAR_SPEED = 0.03  # Cap global rotation (rad/frame)

# START-UP DELAY - waits for SLAM to be ready before enabling autonomy
STARTUP_DELAY_SECONDS = 15.0  # ⏱️ 15 seconds to let SLAM initialise completely

# AUTOMATIC STOP ON RETURN - to map a complete lap
ENABLE_AUTO_STOP = True        # 🔄 True = 2-phase automatic stop (return then +2m), False = continuous loop
AUTO_STOP_DISTANCE = 0.05      # Distance to the start for the automatic stop (metres)
MIN_DISTANCE_TRAVELED = 3.0   # Minimum distance before stopping is allowed (avoids an immediate stop)
EXTRA_DISTANCE_AFTER_RETURN = 2.0  # Distance to drive AFTER returning to the start before stopping (metres)
LEAVE_START_DISTANCE = 0.60    # Must first move away from the start before a return can be validated
RETURN_DETECTION_DISTANCE = 0.20  # Detection tolerance for passing the start
LAP_SAMPLE_DISTANCE = 0.08        # Sampling of the trajectory points during the lap
NAV2_WAYPOINT_SPACING = 0.30      # Minimum spacing between waypoints sent to Nav2
NAV2_SAFE_WAYPOINT_SPACING = 0.45  # Wider spacing to avoid points that are too close
NAV2_ENTRY_LOOKAHEAD_M = 1.2      # Entry point in the right direction before returning to the start
NAV2_ROUTE_GOAL_SPACING = 1.20    # Spacing of the sequential NavigateToPose goals

# SIMPLE MODE: return without Nav2 (A* + PID following)
USE_SIMPLE_ASTAR_RETURN = True
SIMPLE_ASTAR_CELL_PX = 4
SIMPLE_ASTAR_INFLATION_CELLS = 3
SIMPLE_LOOKAHEAD_PX = 10.0
SIMPLE_GOAL_TOLERANCE_PX = 12.0
SIMPLE_KP_HEADING = 1.8
SIMPLE_KD_HEADING = 0.25
SIMPLE_MAX_SPEED_PX = 0.72   # Higher speed ONLY while following a computed trajectory
SIMPLE_FULL_LOOP_SPACING_M = 0.18
SIMPLE_SHORTCUT_CLEARANCE_PX = 10
SIMPLE_SHORTCUT_MAX_SKIP = 80
SIMPLE_FINAL_BRAKE_RADIUS_PX = 40.0
SIMPLE_REQUIRE_FULL_LOOP = True
SIMPLE_ALLOW_ASTAR_FALLBACK = False
SIMPLE_MIN_PATH_KEEP_RATIO = 0.55

auto_mode = False         # ⏳ Starts in MANUAL mode, switches to auto after the delay
startup_timer = 0.0       # Counter that enables auto mode after the delay
max_distance_reached = 0.0  # Max distance reached from the start
prev_w = 0.0              # Previous rotation (filter)
loop_return_detected = False
extra_distance_after_return = 0.0
has_left_start_zone = False
nav2_mode = False
last_robot_pos_for_stop = robot_pos.copy()

nav2_cmd_linear_m_s = 0.0
nav2_cmd_angular_rad_s = 0.0
nav2_last_cmd_time = 0.0
nav2_status = "IDLE"
nav2_goal_pending = False
nav2_goal_last_try = 0.0
nav2_plan_points_m = []
nav2_requested_waypoints_m = []
nav2_route_goals_m = []
nav2_route_goal_idx = 0

simple_return_mode = False
simple_path_px = []
simple_path_idx = 0
simple_prev_heading_err = 0.0
simple_status = "IDLE"

slam_freeze_requested = False
slam_freeze_pose_x = None  # Holds the robot position when SLAM freezes
slam_freeze_pose_y = None
slam_freeze_pose_theta = None

lap_points_m = []
lap_recording_started = False
lap_recording_done = False
last_lap_sample_pos_m = None
lap_start_point_m = None

class Nav2InterfaceNode(Node):
    def __init__(self):
        super().__init__('simu_nav2_interface')
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_cb, 10)
        self.create_subscription(Path, '/plan', self.plan_cb, 10)
        self.create_subscription(OccupancyGrid, '/map', self.map_cb, 10)
        self.create_subscription(TFMessage, '/tf', self.tf_cb, 50)
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.nav_through_client = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')
        self.map_msg = None
        self.tf_broadcaster = TransformBroadcaster(self)
        self.latest_map_odom_transform = None

    def cmd_vel_cb(self, msg):
        global nav2_cmd_linear_m_s, nav2_cmd_angular_rad_s, nav2_last_cmd_time
        nav2_cmd_linear_m_s = float(msg.linear.x)
        nav2_cmd_angular_rad_s = float(msg.angular.z)
        nav2_last_cmd_time = time.time()

    def plan_cb(self, msg):
        global nav2_plan_points_m
        nav2_plan_points_m = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]

    def map_cb(self, msg):
        self.map_msg = msg

    def tf_cb(self, msg):
        for tf in msg.transforms:
            if tf.header.frame_id == 'map' and tf.child_frame_id == 'odom':
                self.latest_map_odom_transform = tf

    def world_to_map(self, x_m, y_m):
        if self.map_msg is None:
            return None
        info = self.map_msg.info
        mx = int((x_m - info.origin.position.x) / info.resolution)
        my = int((y_m - info.origin.position.y) / info.resolution)
        if mx < 0 or my < 0 or mx >= info.width or my >= info.height:
            return None
        return mx, my

    def map_to_world(self, mx, my):
        info = self.map_msg.info
        x = info.origin.position.x + (mx + 0.5) * info.resolution
        y = info.origin.position.y + (my + 0.5) * info.resolution
        return x, y

    def is_free(self, mx, my):
        info = self.map_msg.info
        idx = my * info.width + mx
        value = int(self.map_msg.data[idx])
        return value >= 0 and value <= 40

    def find_nearest_free_goal(self, x_m, y_m, search_radius_cells=30):
        if self.map_msg is None:
            return x_m, y_m

        start_cell = self.world_to_map(x_m, y_m)
        if start_cell is None:
            return x_m, y_m
        sx, sy = start_cell

        if self.is_free(sx, sy):
            return x_m, y_m

        best = None
        best_d2 = 1e18
        for r in range(1, search_radius_cells + 1):
            xmin = max(0, sx - r)
            xmax = min(self.map_msg.info.width - 1, sx + r)
            ymin = max(0, sy - r)
            ymax = min(self.map_msg.info.height - 1, sy + r)

            for mx in range(xmin, xmax + 1):
                for my in (ymin, ymax):
                    if self.is_free(mx, my):
                        d2 = (mx - sx) * (mx - sx) + (my - sy) * (my - sy)
                        if d2 < best_d2:
                            best_d2 = d2
                            best = (mx, my)
            for my in range(ymin + 1, ymax):
                for mx in (xmin, xmax):
                    if self.is_free(mx, my):
                        d2 = (mx - sx) * (mx - sx) + (my - sy) * (my - sy)
                        if d2 < best_d2:
                            best_d2 = d2
                            best = (mx, my)

            if best is not None:
                bx, by = best
                return self.map_to_world(bx, by)

        return x_m, y_m

    def is_clearance_free(self, x_m, y_m, clearance_cells=2):
        if self.map_msg is None:
            return True

        cell = self.world_to_map(x_m, y_m)
        if cell is None:
            return False
        cx, cy = cell

        info = self.map_msg.info
        for dx in range(-clearance_cells, clearance_cells + 1):
            for dy in range(-clearance_cells, clearance_cells + 1):
                mx = cx + dx
                my = cy + dy
                if mx < 0 or my < 0 or mx >= info.width or my >= info.height:
                    return False
                if not self.is_free(mx, my):
                    return False
        return True

    def _on_goal_response(self, future):
        global nav2_status
        try:
            goal_handle = future.result()
            if goal_handle is None or not goal_handle.accepted:
                nav2_status = 'GOAL_REJECTED'
                self.get_logger().warning('Goal rejected by Nav2')
                return
            nav2_status = 'GOAL_ACCEPTED'
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self._on_nav_result)
        except Exception as ex:
            nav2_status = f'GOAL_RESP_ERR: {type(ex).__name__}'
            self.get_logger().warning(f'Goal response error: {ex}')

    def _on_nav_result(self, future):
        global nav2_status
        try:
            result = future.result()
            status_code = int(result.status)
            if status_code == 4:
                nav2_status = 'GOAL_SUCCEEDED'
            elif status_code == 6:
                nav2_status = 'GOAL_ABORTED'
            elif status_code == 5:
                nav2_status = 'GOAL_CANCELED'
            else:
                nav2_status = f'GOAL_DONE_{status_code}'
        except Exception as ex:
            nav2_status = f'GOAL_RES_ERR: {type(ex).__name__}'
            self.get_logger().warning(f'Goal result error: {ex}')

    def publish_frozen_map_to_odom_transform(self):
        """Re-publishes map->odom with a fresh timestamp while SLAM is frozen."""
        try:
            if not rclpy.ok():
                return
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = 'map'
            t.child_frame_id = 'odom'

            if self.latest_map_odom_transform is not None:
                src = self.latest_map_odom_transform
                t.transform.translation.x = src.transform.translation.x
                t.transform.translation.y = src.transform.translation.y
                t.transform.translation.z = src.transform.translation.z
                t.transform.rotation.x = src.transform.rotation.x
                t.transform.rotation.y = src.transform.rotation.y
                t.transform.rotation.z = src.transform.rotation.z
                t.transform.rotation.w = src.transform.rotation.w
            else:
                t.transform.translation.x = 0.0
                t.transform.translation.y = 0.0
                t.transform.translation.z = 0.0
                t.transform.rotation.x = 0.0
                t.transform.rotation.y = 0.0
                t.transform.rotation.z = 0.0
                t.transform.rotation.w = 1.0

            self.tf_broadcaster.sendTransform(t)
        except Exception as e:
            if 'context is invalid' in str(e):
                return
            self.get_logger().warning(f'Error publishing frozen transform: {e}')
    def send_goal_to_start(self, x_m, y_m, yaw_rad):
        global nav2_status
        try:
            if not rclpy.ok():
                nav2_status = "ROS_CONTEXT_DOWN"
                return False

            if not self.nav_client.wait_for_server(timeout_sec=1.0):
                nav2_status = "WAIT_ACTION_SERVER"
                self.get_logger().warning('Nav2 action server /navigate_to_pose unavailable (retry)')
                return False

            gx, gy = self.find_nearest_free_goal(x_m, y_m)

            goal_msg = NavigateToPose.Goal()
            goal_msg.pose.header.frame_id = 'map'
            goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
            goal_msg.pose.pose.position.x = float(gx)
            goal_msg.pose.pose.position.y = float(gy)
            goal_msg.pose.pose.position.z = 0.0

            half = yaw_rad / 2.0
            goal_msg.pose.pose.orientation.z = math.sin(half)
            goal_msg.pose.pose.orientation.w = math.cos(half)

            self.get_logger().info(
                f'🎯 Sending Nav2 goal (return to start): x={gx:.3f} y={gy:.3f} yaw={yaw_rad:.3f}'
            )
            send_future = self.nav_client.send_goal_async(goal_msg)
            send_future.add_done_callback(self._on_goal_response)
            nav2_status = "GOAL_SENT"
            return True
        except Exception as ex:
            nav2_status = f"GOAL_SEND_ERR: {type(ex).__name__}"
            self.get_logger().warning(f'Nav2 goal send failed (retry): {ex}')
            return False

    def send_through_poses(self, points_m):
        global nav2_status, nav2_requested_waypoints_m
        try:
            if not rclpy.ok():
                nav2_status = "ROS_CONTEXT_DOWN"
                return False

            if not self.nav_through_client.wait_for_server(timeout_sec=1.0):
                nav2_status = "WAIT_THROUGH_SERVER"
                self.get_logger().warning('Nav2 action server /navigate_through_poses unavailable (retry)')
                return False

            goal_msg = NavigateThroughPoses.Goal()
            poses = []
            now = self.get_clock().now().to_msg()

            sanitized_points = []
            for x_m, y_m in points_m:
                gx, gy = self.find_nearest_free_goal(x_m, y_m, search_radius_cells=20)
                if self.is_clearance_free(gx, gy, clearance_cells=2):
                    sanitized_points.append((gx, gy))

            if len(sanitized_points) >= 2:
                reduced = [sanitized_points[0]]
                for point in sanitized_points[1:]:
                    if distance_m(point[0], point[1], reduced[-1][0], reduced[-1][1]) >= NAV2_SAFE_WAYPOINT_SPACING:
                        reduced.append(point)
                if distance_m(reduced[-1][0], reduced[-1][1], sanitized_points[-1][0], sanitized_points[-1][1]) > 0.10:
                    reduced.append(sanitized_points[-1])
                sanitized_points = reduced

            nav2_requested_waypoints_m = sanitized_points

            for idx, (x_m, y_m) in enumerate(sanitized_points):
                pose = PoseStamped()
                pose.header.frame_id = 'map'
                pose.header.stamp = now
                pose.pose.position.x = float(x_m)
                pose.pose.position.y = float(y_m)
                pose.pose.position.z = 0.0

                if idx < len(sanitized_points) - 1:
                    nx, ny = sanitized_points[idx + 1]
                    yaw = math.atan2(ny - y_m, nx - x_m)
                else:
                    yaw = 0.0
                pose.pose.orientation.z = math.sin(yaw / 2.0)
                pose.pose.orientation.w = math.cos(yaw / 2.0)
                poses.append(pose)

            if len(poses) < 2:
                nav2_status = "TOO_FEW_WAYPOINTS"
                return False

            goal_msg.poses = poses
            self.get_logger().info(f'🧭 Sending NavigateThroughPoses with {len(poses)} waypoints')
            send_future = self.nav_through_client.send_goal_async(goal_msg)
            send_future.add_done_callback(self._on_goal_response)
            nav2_status = "THROUGH_SENT"
            return True
        except Exception as ex:
            nav2_status = f"THROUGH_ERR: {type(ex).__name__}"
            self.get_logger().warning(f'NavigateThroughPoses failed (retry): {ex}')
            return False

def start_nav2_interface():
    if not ROS2_AVAILABLE:
        return None
    try:
        rclpy.init(args=None)
    except Exception:
        pass

    node = Nav2InterfaceNode()

    def spin_node():
        try:
            rclpy.spin(node)
        except Exception:
            pass

    thread = threading.Thread(target=spin_node, daemon=True)
    thread.start()
    return node

nav2_interface = start_nav2_interface()

def get_lidar_ranges(pos, theta):
    ranges = []
    max_range = 2.0  # LIDAR range (m)
    for i in range(NUM_RAYS):
        angle = (2.0 * math.pi * i / NUM_RAYS) + theta
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        dist = max_range
        # Step=1 instead of 2 so that no pixel is skipped in the corners
        for r in range(5, int(max_range/MAP_RES), 1):
            tx, ty = int(pos[0] + r*cos_a), int(pos[1] + r*sin_a)
            if not (0 <= tx < WIDTH and 0 <= ty < HEIGHT) or circuit_surf.get_at((tx, ty))[0] < 80:
                dist = r * MAP_RES
                break
        ranges.append(float(dist))
    return ranges

def distance_m(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def is_track_free_px(px, py):
    if px < 0 or py < 0 or px >= WIDTH or py >= HEIGHT:
        return False
    return circuit_surf.get_at((int(px), int(py)))[0] >= 80

def is_track_free_with_clearance_px(px, py, clearance_px):
    if not is_track_free_px(px, py):
        return False
    step = max(2, clearance_px // 3)
    for oy in range(-clearance_px, clearance_px + 1, step):
        for ox in range(-clearance_px, clearance_px + 1, step):
            if (ox * ox + oy * oy) <= (clearance_px * clearance_px):
                if not is_track_free_px(px + ox, py + oy):
                    return False
    return True

def is_segment_clear_with_clearance(p1, p2, clearance_px):
    x1, y1 = p1
    x2, y2 = p2
    dist = math.hypot(x2 - x1, y2 - y1)
    steps = max(2, int(dist / 3.0))
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if not is_track_free_with_clearance_px(x, y, clearance_px):
            return False
    return True

def is_cell_free(cx, cy, cell_px, inflation_cells):
    center_x = cx * cell_px + cell_px // 2
    center_y = cy * cell_px + cell_px // 2
    for oy in range(-inflation_cells, inflation_cells + 1):
        for ox in range(-inflation_cells, inflation_cells + 1):
            px = center_x + ox * cell_px
            py = center_y + oy * cell_px
            if not is_track_free_px(px, py):
                return False
    return True

def plan_astar_path_px(start_px, goal_px, cell_px=SIMPLE_ASTAR_CELL_PX, inflation_cells=SIMPLE_ASTAR_INFLATION_CELLS):
    grid_w = WIDTH // cell_px
    grid_h = HEIGHT // cell_px

    sx, sy = int(start_px[0] // cell_px), int(start_px[1] // cell_px)
    gx, gy = int(goal_px[0] // cell_px), int(goal_px[1] // cell_px)

    sx = max(0, min(grid_w - 1, sx))
    sy = max(0, min(grid_h - 1, sy))
    gx = max(0, min(grid_w - 1, gx))
    gy = max(0, min(grid_h - 1, gy))

    if not is_cell_free(gx, gy, cell_px, inflation_cells):
        return []

    open_heap = []
    heapq.heappush(open_heap, (0.0, (sx, sy)))
    g_score = {(sx, sy): 0.0}
    parent = {}

    neighbors = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)
    ]

    def heuristic(ax, ay, bx, by):
        return math.hypot(ax - bx, ay - by)

    visited = set()
    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)

        if current == (gx, gy):
            path_cells = [current]
            while current in parent:
                current = parent[current]
                path_cells.append(current)
            path_cells.reverse()
            path_px = []
            for cx, cy in path_cells:
                path_px.append((cx * cell_px + cell_px // 2, cy * cell_px + cell_px // 2))
            return path_px

        cx, cy = current
        for dx, dy, cost in neighbors:
            nx, ny = cx + dx, cy + dy
            if nx < 0 or ny < 0 or nx >= grid_w or ny >= grid_h:
                continue
            if not is_cell_free(nx, ny, cell_px, inflation_cells):
                continue

            tentative = g_score[(cx, cy)] + cost
            if (nx, ny) not in g_score or tentative < g_score[(nx, ny)]:
                g_score[(nx, ny)] = tentative
                parent[(nx, ny)] = (cx, cy)
                f = tentative + heuristic(nx, ny, gx, gy)
                heapq.heappush(open_heap, (f, (nx, ny)))

    return []

def compute_simple_follow_command(robot_pos_px, robot_theta_rad, dt_s):
    global simple_path_px, simple_path_idx, simple_prev_heading_err, simple_status

    if len(simple_path_px) == 0:
        simple_status = "NO_PATH"
        return 0.0, 0.0, True

    while simple_path_idx < len(simple_path_px) - 1:
        tx, ty = simple_path_px[simple_path_idx]
        if math.hypot(tx - robot_pos_px[0], ty - robot_pos_px[1]) < SIMPLE_LOOKAHEAD_PX:
            simple_path_idx += 1
        else:
            break

    tx, ty = simple_path_px[simple_path_idx]
    dist = math.hypot(tx - robot_pos_px[0], ty - robot_pos_px[1])
    final_tx, final_ty = simple_path_px[-1]
    final_dist = math.hypot(final_tx - robot_pos_px[0], final_ty - robot_pos_px[1])

    if simple_path_idx >= len(simple_path_px) - 1 and final_dist < SIMPLE_GOAL_TOLERANCE_PX:
        simple_status = "REACHED"
        return 0.0, 0.0, True

    desired_heading = math.atan2(ty - robot_pos_px[1], tx - robot_pos_px[0])
    heading_err = normalize_angle(desired_heading - robot_theta_rad)
    dheading = (heading_err - simple_prev_heading_err) / max(1e-3, dt_s)
    simple_prev_heading_err = heading_err

    angular = SIMPLE_KP_HEADING * heading_err + SIMPLE_KD_HEADING * dheading
    angular = float(np.clip(angular, -MAX_ANGULAR_SPEED, MAX_ANGULAR_SPEED))

    heading_scale = max(0.0, 1.0 - min(abs(heading_err), math.pi) / math.pi)
    linear = SIMPLE_MAX_SPEED_PX * (0.25 + 0.75 * heading_scale)
    if dist < SIMPLE_LOOKAHEAD_PX:
        linear *= 0.6

    # Progressive braking at the end to avoid overshooting the last point
    if simple_path_idx >= len(simple_path_px) - 2:
        final_scale = min(1.0, max(0.08, final_dist / SIMPLE_FINAL_BRAKE_RADIUS_PX))
        linear *= final_scale

    if simple_path_idx >= len(simple_path_px) - 1 and final_dist < (1.5 * SIMPLE_GOAL_TOLERANCE_PX):
        linear = min(linear, 0.12)

    simple_status = f"FOLLOW {simple_path_idx+1}/{len(simple_path_px)}"
    return linear, angular, False

def build_forward_loop_waypoints(current_x_m, current_y_m):
    if len(lap_points_m) < 10:
        return []

    nearest_index = 0
    best_d2 = 1e18
    for i, (x_m, y_m) in enumerate(lap_points_m):
        d2 = (x_m - current_x_m) * (x_m - current_x_m) + (y_m - current_y_m) * (y_m - current_y_m)
        if d2 < best_d2:
            best_d2 = d2
            nearest_index = i

    ordered = lap_points_m[nearest_index:] + lap_points_m[:nearest_index]

    sampled = []
    last = None
    for point in ordered:
        if last is None or distance_m(point[0], point[1], last[0], last[1]) >= NAV2_WAYPOINT_SPACING:
            sampled.append(point)
            last = point

    if lap_start_point_m is not None:
        end_x_m, end_y_m = lap_start_point_m
    else:
        end_x_m = start_pos[0] * MAP_RES
        end_y_m = start_pos[1] * MAP_RES
    if len(sampled) == 0 or distance_m(sampled[-1][0], sampled[-1][1], end_x_m, end_y_m) > NAV2_WAYPOINT_SPACING:
        sampled.append((end_x_m, end_y_m))

    return sampled

def choose_entry_waypoint_from_lap(current_x_m, current_y_m, lookahead_m=NAV2_ENTRY_LOOKAHEAD_M):
    if len(lap_points_m) < 10:
        return None

    nearest_index = 0
    best_d2 = 1e18
    for i, (x_m, y_m) in enumerate(lap_points_m):
        d2 = (x_m - current_x_m) * (x_m - current_x_m) + (y_m - current_y_m) * (y_m - current_y_m)
        if d2 < best_d2:
            best_d2 = d2
            nearest_index = i

    cumulative = 0.0
    prev = lap_points_m[nearest_index]
    i = nearest_index + 1
    while i < len(lap_points_m):
        cur = lap_points_m[i]
        cumulative += distance_m(prev[0], prev[1], cur[0], cur[1])
        if cumulative >= lookahead_m:
            return cur
        prev = cur
        i += 1

    return lap_points_m[-1]

def build_nav2_sequential_route_goals(current_x_m, current_y_m):
    if len(lap_points_m) < 10:
        return []

    # The start is forced within the beginning of the recorded trajectory,
    # because the switch to Nav2 happens right after passing the start +2m.
    # This avoids "jumping" to a close point that faces the wrong way.
    search_end = max(5, int(0.45 * len(lap_points_m)))
    nearest_index = 0
    best_d2 = 1e18
    for i in range(search_end):
        x_m, y_m = lap_points_m[i]
        d2 = (x_m - current_x_m) * (x_m - current_x_m) + (y_m - current_y_m) * (y_m - current_y_m)
        if d2 < best_d2:
            best_d2 = d2
            nearest_index = i

    forward = lap_points_m[nearest_index:]
    sampled = []
    last = None
    for point in forward:
        if last is None or distance_m(point[0], point[1], last[0], last[1]) >= NAV2_ROUTE_GOAL_SPACING:
            sampled.append(point)
            last = point

    if lap_start_point_m is not None:
        sx, sy = lap_start_point_m
    else:
        sx = start_pos[0] * MAP_RES
        sy = start_pos[1] * MAP_RES

    if len(sampled) == 0 or distance_m(sampled[-1][0], sampled[-1][1], sx, sy) > NAV2_ROUTE_GOAL_SPACING:
        sampled.append((sx, sy))

    return sampled

def build_simple_full_loop_path_px(current_x_m, current_y_m):
    if len(lap_points_m) < 10:
        return []

    nearest_index = 0
    best_d2 = 1e18
    for i, (x_m, y_m) in enumerate(lap_points_m):
        d2 = (x_m - current_x_m) * (x_m - current_x_m) + (y_m - current_y_m) * (y_m - current_y_m)
        if d2 < best_d2:
            best_d2 = d2
            nearest_index = i

    # The goal is to end at the start point (not back at the beginning of the return)
    sx_m = start_pos[0] * MAP_RES
    sy_m = start_pos[1] * MAP_RES
    goal_index = 0
    goal_best_d2 = 1e18
    for i, (x_m, y_m) in enumerate(lap_points_m):
        d2 = (x_m - sx_m) * (x_m - sx_m) + (y_m - sy_m) * (y_m - sy_m)
        if d2 < goal_best_d2:
            goal_best_d2 = d2
            goal_index = i

    # Forward segment: nearest_index -> goal_index (wrapping if needed)
    if nearest_index <= goal_index:
        ordered_loop = lap_points_m[nearest_index:goal_index + 1]
    else:
        ordered_loop = lap_points_m[nearest_index:] + lap_points_m[:goal_index + 1]

    sampled_m = []
    last = None
    for point in ordered_loop:
        if last is None or distance_m(point[0], point[1], last[0], last[1]) >= SIMPLE_FULL_LOOP_SPACING_M:
            sampled_m.append(point)
            last = point

    if len(sampled_m) < 2:
        return []

    if distance_m(sampled_m[-1][0], sampled_m[-1][1], sx_m, sy_m) > SIMPLE_FULL_LOOP_SPACING_M:
        sampled_m.append((sx_m, sy_m))

    path_px = []
    for x_m, y_m in sampled_m:
        px = int(x_m / MAP_RES)
        py = int(y_m / MAP_RES)
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            path_px.append((px, py))

    if len(path_px) < 3:
        return path_px

    raw_len = len(path_px)

    # Optimisation: safe shortcuts that keep the order of the loop
    optimized = [path_px[0]]
    i = 0
    while i < len(path_px) - 1:
        best_next = i + 1
        # Strict limit on the jump to avoid "cutting" a large part of the loop
        j_max = min(len(path_px) - 1, i + min(SIMPLE_SHORTCUT_MAX_SKIP, 16))
        for j in range(j_max, i + 1, -1):
            if is_segment_clear_with_clearance(path_px[i], path_px[j], SIMPLE_SHORTCUT_CLEARANCE_PX):
                best_next = j
                break
        optimized.append(path_px[best_next])
        i = best_next

    # If the optimisation is too aggressive, keep the raw sampled version
    if len(optimized) < max(3, int(raw_len * SIMPLE_MIN_PATH_KEEP_RATIO)):
        optimized = list(path_px)

    # Light smoothing (moving average) that leaves the end points untouched
    smoothed = [optimized[0]]
    for k in range(1, len(optimized) - 1):
        x = int((optimized[k - 1][0] + optimized[k][0] + optimized[k + 1][0]) / 3)
        y = int((optimized[k - 1][1] + optimized[k][1] + optimized[k + 1][1]) / 3)
        if is_track_free_with_clearance_px(x, y, max(2, SIMPLE_SHORTCUT_CLEARANCE_PX // 2)):
            smoothed.append((x, y))
        else:
            smoothed.append(optimized[k])
    smoothed.append(optimized[-1])

    return smoothed

def stop_slam_and_freeze_map(robot_x_m=None, robot_y_m=None, robot_theta_rad=None):
    global slam_freeze_requested, slam_freeze_pose_x, slam_freeze_pose_y, slam_freeze_pose_theta
    try:
        import subprocess
        import time
        if robot_x_m is not None:
            slam_freeze_pose_x = robot_x_m
            slam_freeze_pose_y = robot_y_m
            slam_freeze_pose_theta = robot_theta_rad
        subprocess.run(['ros2', 'service', 'call', '/freeze_scan', 'std_srvs/srv/Empty'], timeout=2, capture_output=True)
        print("🔒 freeze_scan service called - SLAM and map frozen")
        time.sleep(0.5)
        slam_freeze_requested = True
    except Exception as ex:
        print(f"⚠️ Could not call freeze_scan: {ex}")
        slam_freeze_requested = True
def autonomous_control(ranges):
    """
    Corridor centring logic (SAME AS wall_centering_node)
    Returns: (linear_speed, angular_speed)
    """
    global prev_w
    
    ranges = np.array(ranges)
    # IMPORTANT: no upper limit! Only invalid values are capped at 2.0m
    # As in wall_centering_node: ranges = np.where(np.isfinite(ranges) & (ranges > 0.15), ranges, 2.0)
    ranges = np.where((ranges > 0.15) & np.isfinite(ranges), ranges, 2.0)
    
    # In this simulator: ray 0 = front (angle robot_th)
    idx_front = 0
    
    # Look at the sides (60°) but with a NARROW WINDOW
    # so that distant walls do not get in the way in turns
    side_angle = NUM_RAYS // 6      # 60° = 180/6 = 30 rays (side direction)
    window = int(NUM_RAYS * 10 / 180)  # REDUCED to 10° (instead of 20°) to see only the NEAREST wall
    
    # Same indices as before (this worked better)
    idx_left = (idx_front - side_angle) % NUM_RAYS
    idx_right = (idx_front + side_angle) % NUM_RAYS
    
    # Distance to the side walls (average over ±10° only)
    # This avoids seeing the far wall of the turn while zigzagging
    left_start = (idx_left - window) % NUM_RAYS
    left_end = (idx_left + window) % NUM_RAYS
    right_start = (idx_right - window) % NUM_RAYS
    right_end = (idx_right + window) % NUM_RAYS
    
    # Circular index handling
    if left_start < left_end:
        dist_l = np.mean(ranges[left_start:left_end])
    else:
        dist_l = np.mean(np.concatenate([ranges[left_start:], ranges[:left_end]]))
    
    if right_start < right_end:
        dist_r = np.mean(ranges[right_start:right_end])
    else:
        dist_r = np.mean(np.concatenate([ranges[right_start:], ranges[:right_end]]))
    
    # Distance ahead to brake when the turn is too tight (±10 rays)
    dist_f = np.mean(ranges[max(0, idx_front-10):min(NUM_RAYS, idx_front+10)])
    
    # --- SIMPLE LOGIC (AS IN WALL_CENTERING_NODE) ---
    # No complicated modes, just progressive centring
    error = dist_l - dist_r
    
    if abs(error) < DEADZONE:
        target_w = 0.0
    else:
        # Very gentle proportional correction
        target_w = -error * GAIN_ROT
        if abs(target_w) < MIN_ROTATION:
            target_w = np.sign(target_w) * MIN_ROTATION
    
    emergency_mode = False
    warning_mode = False
    
    # --- ANTI-ZIGZAG FILTER (SIMPLE, AS IN WALL_CENTERING) ---
    smoothed_w = (ALPHA_ROT * prev_w) + ((1 - ALPHA_ROT) * target_w)
    
    # Limit the rotational acceleration
    max_delta = 0.04  # As in wall_centering_node
    diff = smoothed_w - prev_w
    if abs(diff) > max_delta:
        smoothed_w = prev_w + np.sign(diff) * max_delta
    
    prev_w = smoothed_w
    
    # Linear speed (SIMPLE: only slows down when there is a wall ahead)
    if dist_f > 0.8:
        speed = CRUISE_SPEED
    else:
        speed = CRUISE_SPEED * 0.7   # Slower when there is a wall ahead
    
    # Limit the rotation with the global cap
    rotation = np.clip(smoothed_w, -MAX_ANGULAR_SPEED, MAX_ANGULAR_SPEED)
    speed = min(speed, MAX_LINEAR_SPEED)
    
    return speed, rotation, dist_l, dist_r, dist_f, emergency_mode, warning_mode

def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle

def angle_to_quaternion(angle):
    half_angle = angle / 2.0
    return {'z': math.sin(half_angle), 'w': math.cos(half_angle)}

def draw_hud(auto_mode, speed, rotation, dist_l, dist_r, dist_f, emergency_mode=False, warning_mode=False, dist_to_start=0, startup_timer=0, startup_delay=5.0, nav2_mode=False, simple_mode=False):
    """Displays the debug information"""
    y_offset = 10
    
    # Show a countdown while not yet in auto mode
    if not auto_mode and startup_timer < startup_delay:
        remaining = startup_delay - startup_timer
        texts = [
            f"⏳ WAITING FOR SLAM: {remaining:.1f}s left...",
            f"MODE: MANUAL (auto in {remaining:.1f}s)",
            f"🎯 Distance to start: {dist_to_start:.2f}m"
        ]
    else:
        mode_label = 'SIMPLE' if simple_mode else ('NAV2' if nav2_mode else ('AUTONOMOUS' if auto_mode else 'MANUAL'))
        slam_label = '🔒 SLAM FROZEN' if slam_freeze_requested else '🔄 SLAM ACTIVE'
        texts = [
            f"MODE: {mode_label} (A to switch)",
            (f"SIMPLE: {simple_status}" if simple_mode else (f"NAV2: {nav2_status}" if nav2_mode else f"SLAM: {slam_label}")),
            f"Speed: {speed:.2f} px/f ({speed*0.0133*30:.2f} m/s)",
            f"Rotation: {rotation:.3f} rad/s",
            f"[RED=Front] F:{dist_f:.2f}m",
            f"[GREEN=Left] L:{dist_l:.2f}m",
            f"[BLUE=Right] R:{dist_r:.2f}m",
            f"Centring: {(dist_l-dist_r):.2f}m (L-R)",
            f"🎯 Distance to start: {dist_to_start:.2f}m"
        ]
    
    # Add the alerts when needed
    if emergency_mode:
        texts.insert(1, "🚨 CRITICAL EMERGENCY: <0.4m! 🚨")
    elif warning_mode:
        texts.insert(1, "⚠ ALERT: wall close (<0.55m)")
    
    for i, txt in enumerate(texts):
        if i == 0:
            color = (0, 255, 0) if (auto_mode or nav2_mode or simple_mode) else (255, 255, 255)
        elif emergency_mode and i == 1:
            color = (255, 0, 0)  # BRIGHT RED for a critical emergency
        elif warning_mode and i == 1:
            color = (255, 165, 0)  # ORANGE for an alert
        elif i == 3 or ((emergency_mode or warning_mode) and i == 4):
            color = (255, 100, 100)  # Red for F
        elif i == 4 or ((emergency_mode or warning_mode) and i == 5):
            color = (100, 255, 100)  # Green for L
        elif i == 5 or ((emergency_mode or warning_mode) and i == 6):
            color = (100, 100, 255)  # Blue for R
        elif i == 6 or ((emergency_mode or warning_mode) and i == 7):
            error = dist_l - dist_r
            color = (0, 255, 0) if abs(error) < 0.08 else (255, 150, 0)
        else:
            color = (255, 255, 255)
        
        rendered = font.render(txt, True, color, (0, 0, 0))
        screen.blit(rendered, (10, y_offset + i * 20))

# --- MAIN LOOP ---
run = True
speed, rotation, dist_l, dist_r, dist_f = 0, 0, 0, 0, 0
emergency_mode = False
warning_mode = False

while run:
    # ⏱️ AUTO-ACTIVATION AFTER THE DELAY (lets SLAM initialise)
    if not auto_mode and startup_timer < STARTUP_DELAY_SECONDS:
        startup_timer += 1.0/30.0  # Increment (30 FPS)
        if startup_timer >= STARTUP_DELAY_SECONDS:
            auto_mode = True
            print(f"🟢 AUTO MODE ENABLED after {STARTUP_DELAY_SECONDS}s - SLAM ready!")
    
    if not lidar_conn:
        try: 
            lidar_conn, _ = server_sock.accept()
        except: 
            pass

    for e in pygame.event.get():
        if e.type == pygame.QUIT: 
            run = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_a:  # Toggle autonomous mode
                auto_mode = not auto_mode
                nav2_mode = False
                simple_return_mode = False
                prev_w = 0.0  # Reset the filter

    # --- CONTROL ---
    ranges = get_lidar_ranges(robot_pos, robot_th)
    
    if auto_mode:
        # Autonomous mode
        speed, rotation, dist_l, dist_r, dist_f, emergency_mode, warning_mode = autonomous_control(ranges)
        robot_pos[0] += speed * math.cos(robot_th)
        robot_pos[1] += speed * math.sin(robot_th)
        robot_th += rotation
        robot_th = normalize_angle(robot_th)
    elif simple_return_mode:
        # SIMPLE mode: local A* + PID following (without Nav2)
        speed, rotation, reached = compute_simple_follow_command(robot_pos, robot_th, 1.0 / 30.0)
        robot_pos[0] += speed * math.cos(robot_th)
        robot_pos[1] += speed * math.sin(robot_th)
        robot_th += rotation
        robot_th = normalize_angle(robot_th)
        emergency_mode = False
        warning_mode = False
        dist_l, dist_r, dist_f = 0.0, 0.0, 0.0
        if reached:
            simple_return_mode = False
            print("✅ Simple return finished (A* + PID)")
    elif nav2_mode:
        # NAV2 mode: applies /cmd_vel
        if (time.time() - nav2_last_cmd_time) > 0.8:
            cmd_linear = 0.0
            cmd_angular = 0.0
        else:
            cmd_linear = nav2_cmd_linear_m_s
            cmd_angular = nav2_cmd_angular_rad_s

        speed = np.clip(cmd_linear / (MAP_RES * 30.0), -MAX_LINEAR_SPEED, MAX_LINEAR_SPEED)
        rotation = np.clip(cmd_angular / 30.0, -MAX_ANGULAR_SPEED, MAX_ANGULAR_SPEED)
        robot_pos[0] += speed * math.cos(robot_th)
        robot_pos[1] += speed * math.sin(robot_th)
        robot_th += rotation
        robot_th = normalize_angle(robot_th)
        emergency_mode = False
        warning_mode = False
        dist_l, dist_r, dist_f = 0.0, 0.0, 0.0
    else:
        # Manual mode (keyboard)
        k = pygame.key.get_pressed()
        if k[pygame.K_LEFT]:  robot_th -= MAX_ANGULAR_SPEED
        if k[pygame.K_RIGHT]: robot_th += MAX_ANGULAR_SPEED
        if k[pygame.K_UP]:
            robot_pos[0] += MAX_LINEAR_SPEED * math.cos(robot_th)
            robot_pos[1] += MAX_LINEAR_SPEED * math.sin(robot_th)
        speed = MAX_LINEAR_SPEED if k[pygame.K_UP] else 0.0
        rotation = 0.0
        emergency_mode = False
        warning_mode = False
        dist_l, dist_r, dist_f = 0.0, 0.0, 0.0

    # --- DISPLAY ---
    screen.blit(circuit_surf, (0,0))
    
    # Show the detection zones in autonomous mode
    if auto_mode and len(ranges) > 0:
        cx, cy = int(robot_pos[0]), int(robot_pos[1])
        
        # FRONT zone (red)
        for i in range(-10, 10):
            idx = i % NUM_RAYS
            r = ranges[idx]
            if r < 2.0:
                angle = (2.0 * math.pi * idx / NUM_RAYS) + robot_th
                px = int(robot_pos[0] + r*75*math.cos(angle))
                py = int(robot_pos[1] + r*75*math.sin(angle))
                pygame.draw.circle(screen, (255, 0, 0), (px, py), 3)
        
        # LEFT zone (green)
        offset_60deg = NUM_RAYS // 6
        idx_left = -offset_60deg % NUM_RAYS
        for i in range(-10, 10):
            idx = (idx_left + i) % NUM_RAYS
            r = ranges[idx]
            if r < 2.0:
                angle = (2.0 * math.pi * idx / NUM_RAYS) + robot_th
                px = int(robot_pos[0] + r*75*math.cos(angle))
                py = int(robot_pos[1] + r*75*math.sin(angle))
                pygame.draw.circle(screen, (0, 255, 0), (px, py), 3)
        
        # RIGHT zone (blue)
        idx_right = offset_60deg % NUM_RAYS
        for i in range(-10, 10):
            idx = (idx_right + i) % NUM_RAYS
            r = ranges[idx]
            if r < 2.0:
                angle = (2.0 * math.pi * idx / NUM_RAYS) + robot_th
                px = int(robot_pos[0] + r*75*math.cos(angle))
                py = int(robot_pos[1] + r*75*math.sin(angle))
                pygame.draw.circle(screen, (0, 0, 255), (px, py), 3)
    
    # 🎯 START POINT (in YELLOW)
    pygame.draw.circle(screen, (255, 255, 0), (int(start_pos[0]), int(start_pos[1])), 12, 3)  # Hollow yellow circle
    pygame.draw.circle(screen, (255, 255, 0), (int(start_pos[0]), int(start_pos[1])), 5)      # Filled yellow dot

    # 🧭 Waypoints requested from Nav2 (magenta) - visible even if planning fails
    if nav2_mode and len(nav2_requested_waypoints_m) >= 2:
        req_points_px = []
        for px_m, py_m in nav2_requested_waypoints_m:
            px = int(px_m / MAP_RES)
            py = int(py_m / MAP_RES)
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                req_points_px.append((px, py))
        if len(req_points_px) >= 2:
            pygame.draw.lines(screen, (255, 0, 255), False, req_points_px, 2)
            for waypoint in req_points_px[:: max(1, len(req_points_px)//30)]:
                pygame.draw.circle(screen, (220, 0, 220), waypoint, 2)

    # 🟢 A* trajectory of SIMPLE mode
    if simple_return_mode and len(simple_path_px) >= 2:
        pygame.draw.lines(screen, (0, 255, 120), False, simple_path_px, 2)
        if 0 <= simple_path_idx < len(simple_path_px):
            tx, ty = simple_path_px[simple_path_idx]
            pygame.draw.circle(screen, (0, 255, 120), (int(tx), int(ty)), 5)

    # 🧭 Computed Nav2 plan (cyan)
    if nav2_mode and len(nav2_plan_points_m) >= 2:
        plan_points_px = []
        for px_m, py_m in nav2_plan_points_m:
            px = int(px_m / MAP_RES)
            py = int(py_m / MAP_RES)
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                plan_points_px.append((px, py))

        if len(plan_points_px) >= 2:
            pygame.draw.lines(screen, (0, 255, 255), False, plan_points_px, 2)
            for waypoint in plan_points_px[:: max(1, len(plan_points_px)//20)]:
                pygame.draw.circle(screen, (0, 200, 200), waypoint, 2)
    
    # Distance to the start
    dist_to_start = math.sqrt((robot_pos[0]-start_pos[0])**2 + (robot_pos[1]-start_pos[1])**2)
    dist_m = dist_to_start * MAP_RES
    robot_x_m = robot_pos[0] * MAP_RES
    robot_y_m = robot_pos[1] * MAP_RES
    
    # 🔄 2-PHASE AUTOMATIC STOP
    # 1) Detects the return near the start after a complete lap
    # 2) Keeps going for EXTRA_DISTANCE_AFTER_RETURN, then stops
    dx_step = robot_pos[0] - last_robot_pos_for_stop[0]
    dy_step = robot_pos[1] - last_robot_pos_for_stop[1]
    step_m = math.sqrt(dx_step*dx_step + dy_step*dy_step) * MAP_RES
    last_robot_pos_for_stop = robot_pos.copy()

    if auto_mode and dist_m > max_distance_reached:
        max_distance_reached = dist_m

    if ENABLE_AUTO_STOP and auto_mode:
        if dist_m > LEAVE_START_DISTANCE:
            has_left_start_zone = True

        if has_left_start_zone and (not lap_recording_started):
            lap_recording_started = True
            lap_points_m.clear()
            lap_start_point_m = (robot_x_m, robot_y_m)
            last_lap_sample_pos_m = None
            print("📝 Started recording the lap trajectory")

        if lap_recording_started and (not lap_recording_done):
            if (last_lap_sample_pos_m is None) or distance_m(robot_x_m, robot_y_m, last_lap_sample_pos_m[0], last_lap_sample_pos_m[1]) >= LAP_SAMPLE_DISTANCE:
                lap_points_m.append((robot_x_m, robot_y_m))
                last_lap_sample_pos_m = (robot_x_m, robot_y_m)

        if (not loop_return_detected) and has_left_start_zone and max_distance_reached > MIN_DISTANCE_TRAVELED and dist_m < RETURN_DETECTION_DISTANCE:
            loop_return_detected = True
            extra_distance_after_return = 0.0
            lap_recording_done = True
            print(f"\n🎯 RETURN TO START DETECTED! Distance: {dist_m:.2f}m (max reached: {max_distance_reached:.2f}m)")
            print(f"🧭 First-lap trajectory captured: {len(lap_points_m)} points")
            print(f"➡️  Driving {EXTRA_DISTANCE_AFTER_RETURN:.2f}m more to complete the map...")
        elif loop_return_detected:
            extra_distance_after_return += step_m
            if extra_distance_after_return >= EXTRA_DISTANCE_AFTER_RETURN:
                print(
                    f"✅ EXTRA DISTANCE REACHED: {extra_distance_after_return:.2f}m "
                    f"(target {EXTRA_DISTANCE_AFTER_RETURN:.2f}m)"
                )
                print("🧭 Mapping finished: switching to the planned return")
                auto_mode = False
                nav2_mode = False
                simple_return_mode = False
                prev_w = 0.0
                stop_slam_and_freeze_map(robot_pos[0], robot_pos[1], robot_th)

                if USE_SIMPLE_ASTAR_RETURN:
                    simple_path_px = build_simple_full_loop_path_px(robot_x_m, robot_y_m)
                    simple_path_idx = 0
                    simple_prev_heading_err = 0.0
                    if len(simple_path_px) > 1:
                        simple_return_mode = True
                        simple_status = f"LOOP_OK {len(simple_path_px)} pts"
                        print(f"🧭 SIMPLE mode enabled: optimised full lap ({len(simple_path_px)} points)")
                    else:
                        if SIMPLE_REQUIRE_FULL_LOOP and (not SIMPLE_ALLOW_ASTAR_FALLBACK):
                            simple_status = "LOOP_REQUIRED"
                            print("❌ SIMPLE mode: full loop unavailable (A* fallback disabled)")
                            print("➡️  Recording a little longer before switching")
                        else:
                            simple_path_px = plan_astar_path_px((robot_pos[0], robot_pos[1]), (start_pos[0], start_pos[1]))
                            simple_path_idx = 0
                            simple_prev_heading_err = 0.0
                            if len(simple_path_px) > 1:
                                simple_return_mode = True
                                simple_status = f"ASTAR_OK {len(simple_path_px)} pts"
                                print(f"⚠️ Loop unavailable, A* fallback ({len(simple_path_px)} points)")
                            else:
                                simple_status = "PATH_FAIL"
                                print("❌ SIMPLE mode: no path, Nav2 fallback")
                                nav2_mode = True
                else:
                    nav2_mode = True

                nav2_route_goals_m = build_nav2_sequential_route_goals(robot_x_m, robot_y_m)
                nav2_requested_waypoints_m = list(nav2_route_goals_m)
                nav2_route_goal_idx = 0
                if nav2_mode and len(nav2_route_goals_m) > 0:
                    print(f"🧭 Sequential route prepared: {len(nav2_route_goals_m)} NavigateToPose goals")
                    nav2_goal_pending = True
                else:
                    nav2_goal_pending = False
                nav2_goal_last_try = 0.0

    if nav2_mode and (not nav2_goal_pending) and len(nav2_route_goals_m) > 0:
        if nav2_status == 'GOAL_SUCCEEDED':
            nav2_route_goal_idx += 1
            if nav2_route_goal_idx < len(nav2_route_goals_m):
                print(f"✅ Goal {nav2_route_goal_idx}/{len(nav2_route_goals_m)} reached, sending the next one")
                nav2_goal_pending = True
                nav2_goal_last_try = 0.0
            else:
                print("✅ Sequential route finished, back at the start")
        elif nav2_status in ('GOAL_ABORTED', 'GOAL_REJECTED', 'GOAL_CANCELED'):
            nav2_route_goal_idx += 1
            if nav2_route_goal_idx < len(nav2_route_goals_m):
                print(f"⚠️ Goal failed ({nav2_status}), moving on to the next one {nav2_route_goal_idx + 1}/{len(nav2_route_goals_m)}")
                nav2_goal_pending = True
                nav2_goal_last_try = 0.0
            else:
                print(f"❌ Sequential route interrupted: {nav2_status}")

    if nav2_mode and slam_freeze_requested and nav2_interface is not None:
        nav2_interface.publish_frozen_map_to_odom_transform()

    if nav2_mode and nav2_goal_pending and nav2_interface is not None:
        now = time.time()
        if now - nav2_goal_last_try >= 1.0:
            nav2_goal_last_try = now
            if nav2_route_goal_idx < len(nav2_route_goals_m):
                gx, gy = nav2_route_goals_m[nav2_route_goal_idx]
                if nav2_interface.send_goal_to_start(gx, gy, 0.0):
                    print(f"🧭 NavigateToPose sent [{nav2_route_goal_idx + 1}/{len(nav2_route_goals_m)}] x={gx:.2f} y={gy:.2f}")
                    nav2_goal_pending = False
    
    # Robot (blue)
    pygame.draw.circle(screen, (0,0,255), (int(robot_pos[0]), int(robot_pos[1])), 10)
    
    # Red line at the front
    front_x = int(robot_pos[0] + 15 * math.cos(robot_th))
    front_y = int(robot_pos[1] + 15 * math.sin(robot_th))
    pygame.draw.line(screen, (255,0,0), (int(robot_pos[0]), int(robot_pos[1])), (front_x, front_y), 3)
    
    # HUD
    draw_hud(auto_mode, speed, rotation, dist_l, dist_r, dist_f, emergency_mode, warning_mode, dist_m, startup_timer, STARTUP_DELAY_SECONDS, nav2_mode, simple_return_mode)
    
    pygame.display.flip()

    # --- SOCKET SEND ---
    if lidar_conn:
        try:
            q = angle_to_quaternion(robot_th)
            data = {
                'ranges': ranges,
                'pose': {
                    'x': robot_pos[0] * MAP_RES,
                    'y': robot_pos[1] * MAP_RES,
                    'theta': normalize_angle(robot_th),
                    'quaternion': [0, 0, q['z'], q['w']]
                }
            }
            p = pickle.dumps(data)
            lidar_conn.sendall(struct.pack('>I', len(p)) + p)
        except: 
            lidar_conn = None

    clock.tick(30)

pygame.quit()

if nav2_interface is not None:
    try:
        nav2_interface.destroy_node()
    except Exception:
        pass
    try:
        rclpy.shutdown()
    except Exception:
        pass
