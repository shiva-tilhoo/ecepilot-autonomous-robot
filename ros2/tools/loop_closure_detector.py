#!/usr/bin/env python3
"""
LOOP CLOSURE DETECTOR - Detects when the robot comes back to its start point

Listens to the robot pose through TF2 and compares its distance to the start point.
Emits a signal when the loop is complete.

Key parameters:
- RETURN_DETECTION_DISTANCE: distance threshold to detect the return to the start
- MIN_DISTANCE_TRAVELED: minimum distance before detection is allowed
- LEAVE_START_DISTANCE: minimum distance to leave the start area
- LAP_SAMPLE_DISTANCE: sampling interval of the trajectory
"""

import os
import sys
import math
import time
import json
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import TransformListener, Buffer
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, Float32
from std_srvs.srv import Empty

# --- LOOP CLOSURE PARAMETERS ---
RETURN_DETECTION_DISTANCE = 0.20      # Tolerance distance (m) to detect the return
MIN_DISTANCE_TRAVELED = 3.0           # Min distance before detection is allowed (m)
LEAVE_START_DISTANCE = 0.60           # Distance to leave the start area (m)
EXTRA_DISTANCE_AFTER_RETURN = 2.0     # Distance to drive AFTER the return (m)
LAP_SAMPLE_DISTANCE = 0.08            # Trajectory sampling interval (m)
SLAM_MAP_FRAME = "map"
ROBOT_FRAME = "base_link"


class LoopClosureDetector(Node):
    def __init__(self):
        super().__init__('loop_closure_detector')
        
        # TF2 listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Loop closure state
        self.start_pose_x = None
        self.start_pose_y = None
        self.max_distance_reached = 0.0
        self.has_left_start_zone = False
        self.loop_return_detected = False
        self.extra_distance_after_return = 0.0
        self.last_robot_pos = None
        self.last_lap_sample_pos = None
        
        # Recorded trajectory
        self.lap_points_m = []
        self.lap_recording_started = False
        self.lap_recording_done = False
        
        # Publishers
        self.pub_return_detected = self.create_publisher(Bool, '/loop_closure/return_detected', 10)
        self.pub_distance_to_start = self.create_publisher(Float32, '/loop_closure/distance_to_start', 10)
        self.pub_trajectory = self.create_publisher(PoseStamped, '/loop_closure/trajectory_point', 10)
        
        # Timer that checks the pose regularly
        self.create_timer(0.1, self.timer_callback)
        
        self.get_logger().info("🔍 Loop Closure Detector started")
    
    def get_robot_pose_in_map(self):
        """
        Gets the robot pose in the map frame through TF2
        Returns: (x_m, y_m, theta_rad), or None when the TF is not available
        """
        try:
            transform = self.tf_buffer.lookup_transform(
                SLAM_MAP_FRAME,
                ROBOT_FRAME,
                Time()
            )
            
            x = transform.transform.translation.x
            y = transform.transform.translation.y
            
            # Extract the theta angle from the quaternion
            q = transform.transform.rotation
            theta = math.atan2(
                2 * (q.w * q.z + q.x * q.y),
                1 - 2 * (q.y * q.y + q.z * q.z)
            )
            
            return x, y, theta
        except Exception as e:
            return None
    
    def distance_m(self, x1_m, y1_m, x2_m, y2_m):
        """Computes the Euclidean distance in metres"""
        dx = x2_m - x1_m
        dy = y2_m - y1_m
        return math.sqrt(dx*dx + dy*dy)
    
    def timer_callback(self):
        """Periodic (100ms) pose check and loop detection"""
        
        # Get the robot pose
        pose = self.get_robot_pose_in_map()
        if pose is None:
            return
        
        robot_x_m, robot_y_m, robot_theta = pose
        
        # Set the start point on the first call
        if self.start_pose_x is None:
            self.start_pose_x = robot_x_m
            self.start_pose_y = robot_y_m
            self.last_robot_pos = (robot_x_m, robot_y_m)
            self.get_logger().info(f"📍 Start point set: ({robot_x_m:.2f}, {robot_y_m:.2f})")
            return
        
        # Distances
        dist_to_start = self.distance_m(
            robot_x_m, robot_y_m,
            self.start_pose_x, self.start_pose_y
        )
        
        # Publish the distance to the start
        dist_msg = Float32()
        dist_msg.data = dist_to_start
        self.pub_distance_to_start.publish(dist_msg)
        
        # Distance travelled since the last pose
        dx = robot_x_m - self.last_robot_pos[0]
        dy = robot_y_m - self.last_robot_pos[1]
        step_m = math.sqrt(dx*dx + dy*dy)
        self.last_robot_pos = (robot_x_m, robot_y_m)
        
        # Update the max distance reached
        if dist_to_start > self.max_distance_reached:
            self.max_distance_reached = dist_to_start
        
        # === RECORDING & DETECTION LOGIC ===
        
        # Phase 1: start area - wait for the robot to move away
        if not self.has_left_start_zone and dist_to_start > LEAVE_START_DISTANCE:
            self.has_left_start_zone = True
            self.get_logger().info("✅ Robot left the start area, recording starts")
        
        # Phase 2: start recording the trajectory
        if self.has_left_start_zone and not self.lap_recording_started:
            self.lap_recording_started = True
            self.lap_points_m.clear()
            self.last_lap_sample_pos = None
            self.get_logger().info("📝 Started recording the lap trajectory")
        
        # Phase 3: trajectory sampling
        if self.lap_recording_started and not self.lap_recording_done:
            # Sample every LAP_SAMPLE_DISTANCE metres
            if (self.last_lap_sample_pos is None or 
                self.distance_m(
                    robot_x_m, robot_y_m,
                    self.last_lap_sample_pos[0], self.last_lap_sample_pos[1]
                ) >= LAP_SAMPLE_DISTANCE):
                
                self.lap_points_m.append((robot_x_m, robot_y_m))
                self.last_lap_sample_pos = (robot_x_m, robot_y_m)
                
                # Publish the point
                msg = PoseStamped()
                msg.header.frame_id = SLAM_MAP_FRAME
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.pose.position.x = robot_x_m
                msg.pose.position.y = robot_y_m
                msg.pose.position.z = 0.0
                self.pub_trajectory.publish(msg)
        
        # Phase 4: detect the return to the start
        if (not self.loop_return_detected and 
            self.has_left_start_zone and 
            self.max_distance_reached > MIN_DISTANCE_TRAVELED and 
            dist_to_start < RETURN_DETECTION_DISTANCE):
            
            self.loop_return_detected = True
            self.extra_distance_after_return = 0.0
            self.lap_recording_done = True
            
            self.get_logger().info(f"\n🎯 RETURN TO START DETECTED!")
            self.get_logger().info(f"   Distance: {dist_to_start:.2f}m")
            self.get_logger().info(f"   Max reached: {self.max_distance_reached:.2f}m")
            self.get_logger().info(f"   Trajectory captured: {len(self.lap_points_m)} points")
            self.get_logger().info(f"➡️  Driving {EXTRA_DISTANCE_AFTER_RETURN:.2f}m more to complete the map...")
            
            # Publish the detection signal
            ret_msg = Bool()
            ret_msg.data = True
            self.pub_return_detected.publish(ret_msg)
        
        # Phase 5: record the distance after the return
        elif self.loop_return_detected:
            self.extra_distance_after_return += step_m
            
            if self.extra_distance_after_return >= EXTRA_DISTANCE_AFTER_RETURN:
                self.get_logger().info(f"✅ EXTRA DISTANCE REACHED: {self.extra_distance_after_return:.2f}m")
                self.get_logger().info("🧭 Automatic mapping finished")
                self.save_trajectory()
    
    def save_trajectory(self):
        """Saves the recorded trajectory to a file"""
        if not self.lap_points_m:
            self.get_logger().warn("⚠️ No trajectory point to save")
            return
        
        try:
            # Create the trajectories folder if it does not exist
            traj_dir = Path(os.path.dirname(__file__)) / "trajectories"
            traj_dir.mkdir(exist_ok=True)
            
            # Save as JSON
            timestamp = int(time.time())
            traj_file = traj_dir / f"lap_trajectory_{timestamp}.json"
            
            data = {
                "timestamp": timestamp,
                "num_points": len(self.lap_points_m),
                "start_pose": [self.start_pose_x, self.start_pose_y],
                "max_distance": self.max_distance_reached,
                "points": self.lap_points_m  # [(x, y), ...]
            }
            
            with open(traj_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.get_logger().info(f"💾 Trajectory saved: {traj_file}")
            
            # Also save as numpy for fast access
            import numpy as np
            npy_file = traj_dir / f"lap_trajectory_{timestamp}.npy"
            np.save(npy_file, np.array(self.lap_points_m))
            self.get_logger().info(f"💾 Format NPY: {npy_file}")
            
        except Exception as e:
            self.get_logger().error(f"❌ Trajectory save error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = LoopClosureDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
