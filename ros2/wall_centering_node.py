#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import numpy as np
import pygame
import math
import time

class CorridorRailNode(Node):
    def __init__(self):
        super().__init__('corridor_rail_node')
        
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(LaserScan, '/scan', self.callback, 10)
        
        # --- "VIRTUAL RAIL" SETTINGS — TILED FLOOR MODE ---
        self.cruise_speed = 0.4       # Stable nominal speed
        self.alpha_rot = 0.80         # Oscillation damping
        self.deadzone = 0.10          # Unchanged
        self.gain_rot = 1.0           # Angular correction: forces slightly more rotation
        self.min_rotation = 0.38      # Motor threshold: does NOT create a huge turn
        
        self.prev_w = 0.0
        self.last_scan = None
        
        # --- PERIODIC PAUSE FOR SLAM ---
        self.last_pause_time = time.time()
        self.pause_interval_s = 5.0   # Pause every 5 seconds
        self.pause_duration_s = 1.5   # 1.5-second stop
        self.is_paused = False
        self.pause_start_time = None
        
        pygame.init()
        self.screen = pygame.display.set_mode((600, 750))
        self.font = pygame.font.SysFont("monospace", 18, bold=True)

    def callback(self, msg):
        self.last_scan = msg
        self.run_logic()

    def run_logic(self):
        if not self.last_scan: return

        # --- SLAM PAUSE HANDLING ---
        now = time.time()
        
        # Check whether a pause is in progress
        if self.is_paused:
            if now - self.pause_start_time >= self.pause_duration_s:
                # End of the pause, resume
                self.is_paused = False
                self.last_pause_time = now
                self.get_logger().info("✅ SLAM pause over, resuming motion")
            else:
                # Still paused, publish STOP
                stop_cmd = Twist()
                stop_cmd.linear.x = 0.0
                stop_cmd.angular.z = 0.0
                self.pub.publish(stop_cmd)
                return
        
        # Check whether a pause is needed
        if now - self.last_pause_time >= self.pause_interval_s:
            self.is_paused = True
            self.pause_start_time = now
            self.get_logger().info(f"⏸️  PAUSE SLAM ({self.pause_duration_s}s) - Map update")
            # Publish STOP immediately
            stop_cmd = Twist()
            stop_cmd.linear.x = 0.0
            stop_cmd.angular.z = 0.0
            self.pub.publish(stop_cmd)
            return

        ranges = np.array(self.last_scan.ranges)
        # Limit the range to 2.0m: no need to see further in a corridor
        ranges = np.where(np.isfinite(ranges) & (ranges > 0.15), ranges, 2.0)
        
        angle_inc = self.last_scan.angle_increment
        idx_front = int((math.pi/2 - self.last_scan.angle_min) / angle_inc)
        idx_front = 0
        
        # Look wide on the sides (60°) to catch the corridor walls
        side_angle = int(math.radians(60) / angle_inc)
        window = int(math.radians(20) / angle_inc)

        # Measure the distance to the side walls
        dist_l = np.mean(ranges[idx_front + side_angle - window : idx_front + side_angle + window])
        dist_r = np.mean(ranges[idx_front - side_angle - window : idx_front - side_angle + window])
        # Distance ahead to brake when the turn is too tight
        dist_f = np.mean(ranges[idx_front - 10 : idx_front + 10])

        # --- RAIL LOGIC ---
        # If L=0.5 and R=0.5, error=0 (perfectly centred)
        # If L=0.3 and R=0.7, error=-0.4 (too far left, must turn right)
        error = dist_l - dist_r
        
        if abs(error) < self.deadzone:
            target_w = 0.0
        else:
            # Compute a very gentle proportional rotation
            target_w = error * self.gain_rot
            # Apply the motor threshold
            if abs(target_w) < self.min_rotation:
                target_w = np.sign(target_w) * self.min_rotation

        # --- ANTI-ZIGZAG FILTER ---
        # Forbid sudden changes (slew rate limit)
        smoothed_w = (self.alpha_rot * self.prev_w) + ((1 - self.alpha_rot) * target_w)
        
        # Limit the rotational acceleration
        max_delta = 0.1
        diff = smoothed_w - self.prev_w
        if abs(diff) > max_delta:
            smoothed_w = self.prev_w + np.sign(diff) * max_delta
            
        self.prev_w = smoothed_w

        # Command
        cmd = Twist()
        # Slow down a little when the wall ahead gets closer (tight turn)
        cmd.linear.x = float(self.cruise_speed if dist_f > 0.8 else self.cruise_speed * 0.7)
        cmd.angular.z = float(np.clip(smoothed_w, -1.0, 1.0))
        
        self.pub.publish(cmd)
        self.draw_ui(ranges, idx_front, dist_l, dist_r, cmd)

    def draw_ui(self, ranges, idx_f, dl, dr, cmd):
        self.screen.fill((15, 15, 20))
        cx, cy = 300, 400
        # Corridor display
        for i in range(0, len(ranges), 2):
            r = ranges[i]
            if r >= 2.0: continue
            a = (i - idx_f) * self.last_scan.angle_increment - math.pi/2
            px, py = int(cx + r*150*math.cos(a)), int(cy + r*150*math.sin(a))
            pygame.draw.circle(self.screen, (0, 255, 150), (px, py), 1)

        # Robot
        pygame.draw.rect(self.screen, (255, 255, 255), (cx-10, cy-15, 20, 30), 2)
        
        # HUD
        pygame.draw.rect(self.screen, (40, 40, 50), (0, 0, 600, 110))
        txt_v = self.font.render(f"SPEED : {cmd.linear.x:.2f} m/s", True, (255, 255, 255))
        txt_w = self.font.render(f"DIRECTION : {cmd.angular.z:.3f} rad/s", True, (255, 150, 0))
        txt_pos = self.font.render(f"POSITION L:{dl:.2f}m | R:{dr:.2f}m", True, (100, 255, 100))
        
        self.screen.blit(txt_v, (20, 15))
        self.screen.blit(txt_w, (20, 45))
        self.screen.blit(txt_pos, (20, 75))
        
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: rclpy.shutdown()

def main():
    rclpy.init()
    node = CorridorRailNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Long stop to flush the WiFi
        stop = Twist()
        for _ in range(100):
            node.pub.publish(stop)
            time.sleep(0.02)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()