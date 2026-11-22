#!/usr/bin/env python3
"""
Adaptive Coverage Mapping Node for ROS2
- Plans adaptive spiral movements
- Listens to /scan to avoid obstacles
- Publishes /cmd_vel to drive the motors
- Builds the map in real time
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
import numpy as np
import math
from enum import Enum

class CoverageState(Enum):
    IDLE = 0
    MOVING_FORWARD = 1
    TURNING_LEFT = 2
    TURNING_RIGHT = 3
    ADJUSTING = 4
    COMPLETED = 5

class CoverageNode(Node):
    def __init__(self):
        super().__init__('coverage_node')
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Subscribers
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        
        # Control loop timer
        self.timer = self.create_timer(0.1, self.control_loop)  # 10 Hz
        
        # ============ Coverage Parameters ============
        self.spiral_radius = 0.5          # Initial radius in metres
        self.spiral_max_radius = 5.0      # Max radius
        self.spiral_increment = 0.25      # Radius increment on each loop
        self.forward_speed = 0.3          # m/s
        self.angular_speed = 1.0          # rad/s
        self.obstacle_distance = 0.3      # Minimum distance to obstacles (m)
        
        # ============ State Variables ============
        self.state = CoverageState.IDLE
        self.current_spiral_radius = self.spiral_radius
        self.spiral_angle = 0.0           # 0 to 360 degrees
        self.segments_completed = 0       # Number of segments (8 per loop)
        self.current_segment = 0
        self.coverage_complete = False
        self.start_time = self.get_clock().now()
        
        # ============ Sensor Data ============
        self.last_scan = None
        self.last_map = None
        self.obstacle_detected = False
        self.obstacle_direction = None
        self.min_distance = float('inf')
        
        # ============ Logging ============
        self.get_logger().info("Coverage Node initialized - Spiral mapping ready")
        self.get_logger().info(f"  Spiral radius: {self.spiral_radius} to {self.spiral_max_radius} m")
        self.get_logger().info(f"  Forward speed: {self.forward_speed} m/s")
        self.get_logger().info(f"  Obstacle distance: {self.obstacle_distance} m")
        
        # Auto-start after 1 second
        self.create_timer(1.0, self.start_coverage)
        self.started = False
    
    def start_coverage(self):
        """Starts the mapping automatically"""
        if not self.started:
            self.state = CoverageState.MOVING_FORWARD
            self.started = True
            self.get_logger().info("[COVERAGE] Starting spiral mapping coverage")
    
    def scan_callback(self, msg: LaserScan):
        """Processes the LIDAR data"""
        self.last_scan = msg
        
        # Detect obstacles
        self.detect_obstacles()
    
    def map_callback(self, msg: OccupancyGrid):
        """Processes the occupancy grid map"""
        self.last_map = msg
    
    def detect_obstacles(self):
        """Detects the obstacles in the LIDAR scan"""
        if self.last_scan is None:
            return
        
        scan = self.last_scan
        angles = np.arange(len(scan.ranges)) * scan.angle_increment + scan.angle_min
        ranges = np.array(scan.ranges)
        
        # Clean up the infinities
        ranges[ranges == 0] = float('inf')
        ranges[ranges > scan.range_max] = float('inf')
        
        # Look for close obstacles
        self.min_distance = np.min(ranges[ranges < float('inf')])
        
        # Simple detection: obstacle < threshold means it was seen
        if self.min_distance < self.obstacle_distance:
            self.obstacle_detected = True
            
            # Which direction?
            min_idx = np.argmin(ranges)
            angle = angles[min_idx]
            
            # Classify: front (-30° to +30°), left, right
            if -np.pi/6 < angle < np.pi/6:
                self.obstacle_direction = "FRONT"
            elif angle >= 0:
                self.obstacle_direction = "RIGHT"
            else:
                self.obstacle_direction = "LEFT"
        else:
            self.obstacle_detected = False
            self.obstacle_direction = None
    
    def control_loop(self):
        """Main control loop (10 Hz)"""
        if not self.started:
            return
        
        if self.coverage_complete:
            self.stop_motors()
            return
        
        # State machine
        if self.state == CoverageState.MOVING_FORWARD:
            self.handle_moving_forward()
        
        elif self.state == CoverageState.TURNING_LEFT:
            self.handle_turning_left()
        
        elif self.state == CoverageState.TURNING_RIGHT:
            self.handle_turning_right()
        
        elif self.state == CoverageState.ADJUSTING:
            self.handle_adjusting()
        
        elif self.state == CoverageState.IDLE:
            self.stop_motors()
    
    def handle_moving_forward(self):
        """Move forward along the spiral"""
        
        # Obstacle ahead? Turn
        if self.obstacle_detected and self.obstacle_direction == "FRONT":
            self.get_logger().warn(f"[COVERAGE] Obstacle detected at {self.min_distance:.2f}m, turning")
            self.state = CoverageState.TURNING_RIGHT
            return
        
        # Increment the spiral angle
        angle_increment = 0.1  # rad per timestep (10Hz → ~0.5s per segment)
        self.spiral_angle += angle_increment
        
        # One full loop (2π rad)?
        if self.spiral_angle >= 2 * np.pi:
            self.spiral_angle = 0.0
            self.current_spiral_radius += self.spiral_increment
            self.get_logger().info(f"[COVERAGE] Spiral loop completed, radius now {self.current_spiral_radius:.2f}m")
            
            # Spiral finished?
            if self.current_spiral_radius > self.spiral_max_radius:
                self.get_logger().info("[COVERAGE] Coverage complete!")
                self.coverage_complete = True
                self.state = CoverageState.COMPLETED
                return
        
        # Command forward motion
        cmd = Twist()
        cmd.linear.x = self.forward_speed
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
    
    def handle_turning_left(self):
        """Turn left"""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = self.angular_speed  # Positive = CCW (left)
        self.cmd_vel_pub.publish(cmd)
        
        # After 0.5s, resume forward motion
        if self.spiral_angle % (2 * np.pi) > np.pi / 4:  # 45° covered
            self.state = CoverageState.MOVING_FORWARD
    
    def handle_turning_right(self):
        """Turn right"""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = -self.angular_speed  # Negative = CW (right)
        self.cmd_vel_pub.publish(cmd)
        
        # After 0.5s, resume forward motion
        if self.spiral_angle % (2 * np.pi) < -np.pi / 4:
            self.state = CoverageState.MOVING_FORWARD
    
    def handle_adjusting(self):
        """Adjusts the trajectory based on the map"""
        # TODO: implement a smarter adjustment based on /map
        self.state = CoverageState.MOVING_FORWARD
    
    def stop_motors(self):
        """Stops every motor"""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
    
    def get_elapsed_time(self):
        """Returns the elapsed time"""
        now = self.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9
        return elapsed

def main(args=None):
    rclpy.init(args=args)
    node = CoverageNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Coverage node interrupted")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
