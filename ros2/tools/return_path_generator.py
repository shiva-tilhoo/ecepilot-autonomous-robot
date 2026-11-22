#!/usr/bin/env python3
"""
RETURN PATH GENERATOR - Generates the return path with A* on the real SLAM map

Listens to the SLAM Toolbox OccupancyGrid map and plans an optimal return of the robot
to its start point using A* with optimisations (shortcuts, smoothing).
"""

import heapq
import math
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import TransformListener, Buffer
from nav_msgs.msg import OccupancyGrid, Path as PathMsg
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32MultiArray, Bool
from std_msgs.msg import Header

# --- A* PARAMETERS ---
ASTAR_CELL_SIZE_M = 0.08              # Grid step (m) - 8cm to balance accuracy and speed
ASTAR_INFLATION_CELLS = 4             # Inflation cells around obstacles
ASTAR_OBSTACLE_THRESHOLD = 50         # Threshold above which a cell is occupied (0-100)
ASTAR_SHORTCUT_CLEARANCE_M = 0.30     # Safety distance for shortcuts
ASTAR_SHORTCUT_MAX_SKIP = 20          # Max points skipped by a shortcut
ASTAR_MIN_PATH_KEEP_RATIO = 0.45      # Min ratio of points kept after optimisation
ASTAR_ALLOW_DIAGONAL = True           # Diagonal moves allowed
ASTAR_LOOKUP_TIMEOUT = 2.0            # Timeout lookup TF2


@dataclass
class GridPoint:
    """Point of the A* grid"""
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class ReturnPathGenerator(Node):
    def __init__(self):
        super().__init__('return_path_generator')
        
        # TF2
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Map SLAM
        self.current_map = None
        self.map_resolution = 0.05  # Default, updated later
        self.map_origin_x = 0.0
        self.map_origin_y = 0.0
        self.map_width = 0
        self.map_height = 0
        
        # Start pose (set by the detector)
        self.start_pose_x_m = None
        self.start_pose_y_m = None
        
        # Computed path
        self.planned_path_m = []
        self.planned_path_waypoints = []
        
        # Subscribers
        self.create_subscription(OccupancyGrid, '/map', self.map_callback, 1)
        self.create_subscription(Bool, '/loop_closure/return_detected', 
                                 self.return_detected_callback, 10)
        self.create_subscription(PoseStamped, '/loop_closure/trajectory_point',
                                 self.trajectory_point_callback, 10)
        
        # Publishers
        self.pub_planned_path = self.create_publisher(PathMsg, '/return_path', 10)
        self.pub_waypoints = self.create_publisher(Float32MultiArray, '/return_waypoints', 10)
        
        self.get_logger().info("🗺️  Return Path Generator started")
    
    def map_callback(self, msg):
        """Receives the SLAM map updates"""
        self.current_map = msg.data
        self.map_resolution = msg.info.resolution
        self.map_width = msg.info.width
        self.map_height = msg.info.height
        self.map_origin_x = msg.info.origin.position.x
        self.map_origin_y = msg.info.origin.position.y
    
    def trajectory_point_callback(self, msg):
        """Receives the trajectory points and recomputes if needed"""
        # The start point is set on the first detection
        if self.start_pose_x_m is None:
            self.start_pose_x_m = msg.pose.position.x
            self.start_pose_y_m = msg.pose.position.y
            self.get_logger().info(
                f"🎯 Start point set for the return: ({self.start_pose_x_m:.2f}, {self.start_pose_y_m:.2f})"
            )
    
    def return_detected_callback(self, msg):
        """Called when the return is detected - starts the planning"""
        if msg.data and self.current_map is not None:
            self.get_logger().info("🔄 Planning a return path...")
            self.plan_return_path()
    
    def world_to_grid(self, x_m, y_m):
        """Converts world coordinates (m) to grid coordinates (cells)"""
        grid_x = int((x_m - self.map_origin_x) / self.map_resolution)
        grid_y = int((y_m - self.map_origin_y) / self.map_resolution)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        """Converts grid coordinates to world coordinates"""
        x_m = grid_x * self.map_resolution + self.map_origin_x
        y_m = grid_y * self.map_resolution + self.map_origin_y
        return x_m, y_m
    
    def is_cell_free(self, grid_x, grid_y):
        """Checks whether a cell is free (inflation included)"""
        if not (0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height):
            return False
        
        idx = grid_y * self.map_width + grid_x
        if idx >= len(self.current_map):
            return False
        
        value = self.current_map[idx]
        return value >= 0 and value < ASTAR_OBSTACLE_THRESHOLD
    
    def heuristic(self, x1, y1, x2, y2):
        """Euclidean heuristic for A*"""
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx*dx + dy*dy)
    
    def get_neighbors(self, gx, gy):
        """Gets the neighbours of a cell (4 or 8 directions)"""
        neighbors = [
            (gx + 1, gy, 1.0),      # Right
            (gx - 1, gy, 1.0),      # Left
            (gx, gy + 1, 1.0),      # Down
            (gx, gy - 1, 1.0),      # Up
        ]
        
        if ASTAR_ALLOW_DIAGONAL:
            neighbors.extend([
                (gx + 1, gy + 1, 1.414),  # Diagonal
                (gx + 1, gy - 1, 1.414),
                (gx - 1, gy + 1, 1.414),
                (gx - 1, gy - 1, 1.414),
            ])
        
        return neighbors
    
    def plan_astar(self, start_x, start_y, goal_x, goal_y):
        """
        A* implementation that finds a path from the start to the goal
        Returns a list [(gx, gy), ...] in grid coordinates
        """
        if not self.is_cell_free(start_x, start_y):
            self.get_logger().warn(f"⚠️ Start cell is not free")
            return []
        if not self.is_cell_free(goal_x, goal_y):
            self.get_logger().warn(f"⚠️ Goal cell is not free")
            return []
        
        open_set = []
        heapq.heappush(open_set, (0, (start_x, start_y)))
        came_from = {}
        g_score = {(start_x, start_y): 0}
        f_score = {(start_x, start_y): self.heuristic(start_x, start_y, goal_x, goal_y)}
        
        visited = set()
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == (goal_x, goal_y):
                # Rebuild the path
                path = []
                node = current
                while node in came_from:
                    path.append(node)
                    node = came_from[node]
                path.append((start_x, start_y))
                return path[::-1]
            
            cx, cy = current
            for nx, ny, cost in self.get_neighbors(cx, cy):
                if not self.is_cell_free(nx, ny) or (nx, ny) in visited:
                    continue
                
                tentative_g = g_score[current] + cost
                
                if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative_g
                    f = tentative_g + self.heuristic(nx, ny, goal_x, goal_y)
                    f_score[(nx, ny)] = f
                    heapq.heappush(open_set, (f, (nx, ny)))
        
        self.get_logger().warn("❌ A*: no path found")
        return []
    
    def is_segment_clear(self, x1, y1, x2, y2, clearance_cells=2):
        """Checks whether a line segment is free of obstacles"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx > dy:
            steps = dx
        else:
            steps = dy
        
        if steps == 0:
            return True
        
        for i in range(steps + 1):
            t = i / steps
            px = int(x1 + t * (x2 - x1))
            py = int(y1 + t * (y2 - y1))
            
            # Check the area around the point
            for dx_c in range(-clearance_cells, clearance_cells + 1):
                for dy_c in range(-clearance_cells, clearance_cells + 1):
                    if not self.is_cell_free(px + dx_c, py + dy_c):
                        return False
        
        return True
    
    def optimize_path(self, path_grid):
        """Optimises the path with shortcuts and smoothing"""
        if len(path_grid) < 3:
            return path_grid
        
        # 1. Shortcut detection
        optimized = [path_grid[0]]
        i = 0
        
        while i < len(path_grid) - 1:
            best_next = i + 1
            j_max = min(len(path_grid) - 1, i + ASTAR_SHORTCUT_MAX_SKIP)
            
            for j in range(j_max, i + 1, -1):
                if self.is_segment_clear(
                    path_grid[i][0], path_grid[i][1],
                    path_grid[j][0], path_grid[j][1],
                    ASTAR_INFLATION_CELLS
                ):
                    best_next = j
                    break
            
            optimized.append(path_grid[best_next])
            i = best_next
        
        # Check the minimum ratio
        raw_len = len(path_grid)
        opt_len = len(optimized)
        min_keep = max(3, int(raw_len * ASTAR_MIN_PATH_KEEP_RATIO))
        
        if opt_len < min_keep:
            optimized = list(path_grid)
        
        self.get_logger().info(f"🔧 Optimised path: {raw_len} → {opt_len} points")
        return optimized
    
    def smooth_path(self, path_grid):
        """Smooths the path with a moving average"""
        if len(path_grid) < 3:
            return path_grid
        
        smoothed = [path_grid[0]]
        
        for i in range(1, len(path_grid) - 1):
            x = (path_grid[i-1][0] + path_grid[i][0] + path_grid[i+1][0]) // 3
            y = (path_grid[i-1][1] + path_grid[i][1] + path_grid[i+1][1]) // 3
            
            if self.is_cell_free(x, y):
                smoothed.append((x, y))
            else:
                smoothed.append(path_grid[i])
        
        smoothed.append(path_grid[-1])
        return smoothed
    
    def plan_return_path(self):
        """Plans the complete return path"""
        if self.current_map is None:
            self.get_logger().error("❌ No map available")
            return
        
        # Get the current robot pose
        try:
            transform = self.tf_buffer.lookup_transform(
                "map", "base_link", Time()
            )
            robot_x_m = transform.transform.translation.x
            robot_y_m = transform.transform.translation.y
        except Exception as e:
            self.get_logger().error(f"⚠️ TF lookup failed: {e}")
            return
        
        # Convert to grid coordinates
        start_gx, start_gy = self.world_to_grid(robot_x_m, robot_y_m)
        goal_gx, goal_gy = self.world_to_grid(self.start_pose_x_m, self.start_pose_y_m)
        
        self.get_logger().info(
            f"🧭 A* plan from ({robot_x_m:.2f}, {robot_y_m:.2f}) "
            f"to ({self.start_pose_x_m:.2f}, {self.start_pose_y_m:.2f})"
        )
        
        # A*
        path_grid = self.plan_astar(start_gx, start_gy, goal_gx, goal_gy)
        
        if not path_grid:
            self.get_logger().error("❌ A* found no path")
            return
        
        # Optimisation
        path_grid = self.optimize_path(path_grid)
        path_grid = self.smooth_path(path_grid)
        
        # Convert to world coordinates
        self.planned_path_m = [
            self.grid_to_world(gx, gy) for gx, gy in path_grid
        ]
        
        # Publication
        self.pub_planned_path.publish(self.path_to_ros_msg())
        
        self.get_logger().info(f"✅ Return path planned: {len(self.planned_path_m)} points")
    
    def path_to_ros_msg(self):
        """Converts the path to a ROS Path message"""
        msg = PathMsg()
        msg.header = Header()
        msg.header.frame_id = "map"
        msg.header.stamp = self.get_clock().now().to_msg()
        
        for x_m, y_m in self.planned_path_m:
            ps = PoseStamped()
            ps.header.frame_id = "map"
            ps.header.stamp = self.get_clock().now().to_msg()
            ps.pose.position.x = x_m
            ps.pose.position.y = y_m
            ps.pose.position.z = 0.0
            ps.pose.orientation.w = 1.0
            msg.poses.append(ps)
        
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = ReturnPathGenerator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
