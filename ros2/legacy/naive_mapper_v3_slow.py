#!/usr/bin/env python3
"""
ALGO V3: SLOW rotation with SLAM-friendly feedback

Problem with v2: turns too fast (2.5 rad/s) => SLAM loses the pose
Solution: 
  1) VERY LOW angular speed (0.15-0.25 rad/s)
  2) PD smoothing of the rotations 
  3) Pauses to let SLAM process
  4) LIDAR feedback to validate the rotation
"""

import rclpy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import sys
import termios
import tty
import select
import math
import time
import numpy as np


def get_key():
    """Get a single key press"""
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        return ch
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))


def normalize_angle(angle):
    """Wraps an angle into [-pi, pi]"""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


class SLAMFriendlyController:
    """
    Motion controller tuned for SLAM Toolbox.
    - Slow, steady rotations
    - Rest time between moves
    """
    
    def __init__(self):
        self.mode = "manual"  # "manual" or "auto"
        self.follow_side = "right"
        
        # ===== WALL-FOLLOW PARAMS (KEEP v2) =====
        self.idx_front_deg = 0.0
        self.theta_deg = 50.0
        self.lookahead_L = 0.35
        self.d_ref = 0.45
        self.kp = 2.0
        self.kd = 0.4
        self.v_max = 0.60
        self.v_min = 0.15
        self.w_max = 0.25  # ← DRASTICALLY REDUCED (was 2.5!)
        self.k_turn = 1.0
        self.d_stop = 0.25
        self.d_slow = 0.60
        self.front_half_deg = 10.0
        self.fallback_half_deg = 20.0
        
        # ===== ROTATION CONTROL PARAMS (NEW) =====
        # For slow manual rotations
        self.rotation_speed = 0.15  # rad/s (ultra-slow: 8.6°/s)
        self.rotation_pause = 0.3   # pause between moves for SLAM
        self.slam_settle_time = 0.5 # wait before the next action
        
        # ===== STATE =====
        self.e_prev = 0.0
        self.t_prev = time.time()
        self.emergency_active = False
        self.emergency_until = 0.0
        self.last_action_time = 0.0
        self.rotating_manually = False
        self.rotation_start_time = 0.0
        self.rotation_target_time = 0.0  # total duration
        
    def clamp(self, x, lo, hi):
        return max(lo, min(hi, x))
    
    def get_wall_follow_twist(self, scan):
        """
        Computes the cmd_vel for wall following (algo v2).
        Returns (v, w, valid)
        """
        if scan is None or len(scan.ranges) == 0:
            return 0.0, 0.0, False
        
        N = len(scan.ranges)
        
        def sanitize(r):
            if not math.isfinite(r):
                return math.inf
            if r <= scan.range_min or r >= scan.range_max:
                return math.inf
            return r
        
        def wrap(i):
            return i % N if N > 0 else 0
        
        def angle_to_index(angle_rad):
            i = int(round((angle_rad - scan.angle_min) / scan.angle_increment))
            return wrap(i)
        
        def range_rel_deg(rel_deg):
            front_angle = scan.angle_min + math.radians(self.idx_front_deg)
            angle = front_angle + math.radians(rel_deg)
            idx = angle_to_index(angle)
            return sanitize(scan.ranges[idx])
        
        def sector_min_rel_deg(rel_center_deg, half_deg):
            half_steps = max(1, int(round(math.radians(half_deg) / scan.angle_increment)))
            front_angle = scan.angle_min + math.radians(self.idx_front_deg)
            center_angle = front_angle + math.radians(rel_center_deg)
            center_idx = angle_to_index(center_angle)
            best = math.inf
            for di in range(-half_steps, half_steps + 1):
                r = sanitize(scan.ranges[wrap(center_idx + di)])
                if r < best:
                    best = r
            return best
        
        def emergency_turn_sign():
            left_free = sector_min_rel_deg(+45.0, 10.0)
            right_free = sector_min_rel_deg(-45.0, 10.0)
            return +1.0 if left_free > right_free else -1.0
        
        # ===== SAFETY FIRST =====
        d_front = sector_min_rel_deg(0.0, self.front_half_deg)
        
        if d_front < self.d_stop:
            self.emergency_active = True
            self.emergency_until = time.time() + 0.3
        
        if self.emergency_active:
            if (time.time() < self.emergency_until) or (d_front < self.d_slow):
                return 0.0, emergency_turn_sign() * self.w_max, False
            else:
                self.emergency_active = False
        
        # ===== WALL FOLLOW =====
        theta = math.radians(self.theta_deg)
        
        if self.follow_side == "right":
            rel_b = -90.0
            rel_a = -90.0 + self.theta_deg
            sign = +1.0
        else:
            rel_b = +90.0
            rel_a = +90.0 - self.theta_deg
            sign = -1.0
        
        b = range_rel_deg(rel_b)
        a = range_rel_deg(rel_a)
        valid = math.isfinite(a) and math.isfinite(b)
        
        if valid:
            num = a * math.cos(theta) - b
            den = a * math.sin(theta)
            alpha = math.atan2(num, den)
            d = b * math.cos(alpha)
            d_future = d + self.lookahead_L * math.sin(alpha)
            e = self.d_ref - d_future
            
            dt = time.time() - self.t_prev
            de = (e - self.e_prev) / dt if dt > 1e-3 else 0.0
            self.e_prev = e
            self.t_prev = time.time()
            
            w = sign * (self.kp * e + self.kd * de)
            w = self.clamp(w, -self.w_max, +self.w_max)
        else:
            d_side = sector_min_rel_deg(rel_b, self.fallback_half_deg)
            if not math.isfinite(d_side):
                w = 0.0
            else:
                e = self.d_ref - d_side
                dt = time.time() - self.t_prev
                de = (e - self.e_prev) / dt if dt > 1e-3 else 0.0
                self.e_prev = e
                self.t_prev = time.time()
                w = sign * (self.kp * e + self.kd * de)
                w = self.clamp(w, -self.w_max, +self.w_max)
        
        # Speed scheduling
        v_front = self.v_max * self.clamp((d_front - self.d_stop) / (self.d_slow - self.d_stop), 0.0, 1.0)
        v_turn = self.v_max / (1.0 + self.k_turn * abs(w))
        v = min(v_front, v_turn)
        v = self.clamp(v, self.v_min, self.v_max)
        
        return v, w, True
    
    def start_slow_rotation(self, direction_sign, duration_sec=None):
        """
        Starts a slow rotation.
        direction_sign: +1 (CCW) or -1 (CW)
        duration_sec: if None, keeps going until stopped manually
        """
        self.rotating_manually = True
        self.rotation_start_time = time.time()
        if duration_sec is not None:
            self.rotation_target_time = duration_sec
        else:
            self.rotation_target_time = None
        self.last_action_time = time.time()
        print(f"  🔄 Slow rotation: {direction_sign:+.0f} @ {self.rotation_speed*180/math.pi:.1f}°/s")
    
    def stop_rotation(self):
        """Stops the manual rotation"""
        self.rotating_manually = False
        self.last_action_time = time.time()
        print(f"  ⏸ Pause SLAM: {self.slam_settle_time:.1f}s")
    
    def get_manual_rotation_twist(self):
        """
        Returns the twist for the current slow rotation.
        Also handles the automatic stop when a duration is given.
        """
        if not self.rotating_manually:
            return 0.0, 0.0
        
        elapsed = time.time() - self.rotation_start_time
        
        # If a duration is given, stop automatically
        if self.rotation_target_time is not None and elapsed >= self.rotation_target_time:
            self.stop_rotation()
            return 0.0, 0.0
        
        # Otherwise, keep rotating
        w = self.rotation_speed  # Positive by default, negative when reversed
        return 0.0, w
    
    def is_allowed_to_move(self):
        """Checks whether the robot may move (SLAM delay respected)"""
        elapsed = time.time() - self.last_action_time
        return elapsed >= self.slam_settle_time


def main():
    rclpy.init()
    node = rclpy.create_node('teleop_slow')
    
    cmd_vel_pub = node.create_publisher(Twist, '/cmd_vel', 10)
    
    latest_scan = None
    
    def scan_cb(msg):
        nonlocal latest_scan
        latest_scan = msg
    
    node.create_subscription(LaserScan, '/scan', scan_cb, qos_profile_sensor_data)
    
    controller = SLAMFriendlyController()
    
    print("""
    ╔════════════════════════════════════════════╗
    │   TELEOP V3: SLAM-FRIENDLY SLOW CONTROL   │
    ╠════════════════════════════════════════════╣
    │  W/A/S/D  : SLOW motion/rotation          │
    │  SPACE    : Stop                          │
    │  M        : Toggle AUTO wall-follow       │
    │  R/L      : AUTO wall: RIGHT/LEFT         │
    │  Q        : Quit                          │
    ├────────────────────────────────────────────┤
    │  ⚡ VERY SLOW rotations for SLAM        │
    │  ⏸ Pauses after each action             │
    │  🔍 Tuned wall-follow feedback          │
    ╚════════════════════════════════════════════╝
    """)
    
    twist = Twist()
    
    try:
        while True:
            # Process ROS callbacks
            rclpy.spin_once(node, timeout_sec=0.0)
            
            # ===== AUTO MODE (wall-follow) =====
            if controller.mode == "auto":
                now = time.time()
                if (now - controller.t_prev) >= 0.10:  # 10 Hz
                    v, w, valid = controller.get_wall_follow_twist(latest_scan)
                    twist.linear.x = float(v)
                    twist.angular.z = float(w)
                    cmd_vel_pub.publish(twist)
            
            # ===== SLOW MANUAL ROTATION =====
            if controller.rotating_manually:
                v, w = controller.get_manual_rotation_twist()
                twist.linear.x = 0.0
                twist.angular.z = float(w)
                cmd_vel_pub.publish(twist)
            
            # ===== NON-BLOCKING KEY INPUT =====
            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
            if not rlist:
                time.sleep(0.005)
                continue
            
            key = get_key()
            
            # ===== KEY HANDLING =====
            if key.upper() == 'W':
                if not controller.mode == "auto" and controller.is_allowed_to_move():
                    twist.linear.x = 0.3
                    twist.angular.z = 0.0
                    cmd_vel_pub.publish(twist)
                    controller.last_action_time = time.time()
                    print("→ FORWARD")
            
            elif key.upper() == 'S':
                if not controller.mode == "auto" and controller.is_allowed_to_move():
                    twist.linear.x = -0.3
                    twist.angular.z = 0.0
                    cmd_vel_pub.publish(twist)
                    controller.last_action_time = time.time()
                    print("← BACKWARD")
            
            elif key.upper() == 'A':
                if not controller.mode == "auto" and controller.is_allowed_to_move():
                    if not controller.rotating_manually:
                        controller.start_slow_rotation(+1)
                    else:
                        controller.stop_rotation()
                        twist.linear.x = 0.0
                        twist.angular.z = 0.0
                        cmd_vel_pub.publish(twist)
            
            elif key.upper() == 'D':
                if not controller.mode == "auto" and controller.is_allowed_to_move():
                    if not controller.rotating_manually:
                        controller.start_slow_rotation(-1)
                    else:
                        controller.stop_rotation()
                        twist.linear.x = 0.0
                        twist.angular.z = 0.0
                        cmd_vel_pub.publish(twist)
            
            elif key == ' ':
                controller.mode = "manual"
                controller.emergency_active = False
                controller.rotating_manually = False
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                cmd_vel_pub.publish(twist)
                controller.last_action_time = time.time()
                print("⊙ STOP")
            
            elif key.upper() == 'M':
                controller.mode = "auto" if controller.mode == "manual" else "manual"
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                cmd_vel_pub.publish(twist)
                controller.e_prev = 0.0
                controller.t_prev = time.time()
                controller.last_action_time = time.time()
                print(f"Mode: {controller.mode.upper()}")
            
            elif key.upper() == 'R':
                controller.follow_side = "right"
                print("AUTO wall: RIGHT")
            
            elif key.upper() == 'L':
                controller.follow_side = "left"
                print("AUTO wall: LEFT")
            
            elif key.upper() == 'Q':
                twist.linear.x = 0.0
                twist.angular.z = 0.0
                cmd_vel_pub.publish(twist)
                print("Quitting...")
                break
    
    except KeyboardInterrupt:
        print("\nStopping...")
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        cmd_vel_pub.publish(twist)
    
    rclpy.shutdown()


if __name__ == '__main__':
    main()
