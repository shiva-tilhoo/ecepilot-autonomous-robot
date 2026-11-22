#!/usr/bin/env python3
"""
NAIVE algorithm to improve mapping during rotations without odometry.

The principle: rotations are detected with the LIDAR itself.
- A "signature" of the scan is saved (angles of the wall peaks)
- The robot turns until it finds that signature again, rotated
"""

import rclpy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data
import math
import numpy as np
import time


def extract_peaks(ranges, angle_increment, angle_min, threshold=0.5):
    """
    Extracts the angular positions of the walls (short-distance peaks).
    Returns a list of angles in radians where walls are detected.
    """
    peaks = []
    for i, r in enumerate(ranges):
        if math.isfinite(r) and r < threshold:
            angle = angle_min + i * angle_increment
            peaks.append(angle)
    return peaks


def normalize_angle(angle):
    """Wraps an angle into [-pi, pi]"""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def angle_diff(angle1, angle2):
    """Normalised angle difference"""
    diff = normalize_angle(angle1 - angle2)
    return diff


def estimate_rotation_from_scans(scan_old, scan_new, max_rotation=math.pi/2):
    """
    NAIVE ALGO: compares two scans to estimate the rotation.
    
    Strategy:
    1) Extract the wall peaks in each scan
    2) Find the angular offset that aligns the peaks
    3) That angle = the rotation performed
    """
    peaks_old = extract_peaks(
        scan_old.ranges, 
        scan_old.angle_increment, 
        scan_old.angle_min
    )
    peaks_new = extract_peaks(
        scan_new.ranges,
        scan_new.angle_increment,
        scan_new.angle_min
    )
    
    if len(peaks_old) < 3 or len(peaks_new) < 3:
        return None  # Not enough features
    
    # Convert to numpy to match the angles
    peaks_old_arr = np.array(peaks_old)
    peaks_new_arr = np.array(peaks_new)
    
    # Try several offsets and keep the one that minimises the error
    best_rotation = 0.0
    best_error = float('inf')
    
    # Test rotations from -45° to +45° in 2° steps
    for rot_deg in np.linspace(-45, 45, 45):
        rot = math.radians(rot_deg)
        
        # Apply the candidate rotation to the old peaks
        rotated_old = peaks_old_arr + rot
        
        # Minimum distance from each old peak to the new ones
        errors = []
        for angle_old in rotated_old:
            # Find the closest new peak
            min_dist = min([abs(angle_diff(angle_old, angle_new)) 
                           for angle_new in peaks_new_arr])
            errors.append(min_dist)
        
        avg_error = np.mean(errors)
        
        if avg_error < best_error:
            best_error = avg_error
            best_rotation = rot
    
    # Return the rotation only when the confidence is high enough
    if best_error < math.radians(10):  # Error < 10°
        return best_rotation
    
    return None


class NaiveRotationEstimator:
    """
    Class that tracks the robot rotations through LIDAR scanning.
    """
    
    def __init__(self):
        self.last_scan = None
        self.estimated_heading = 0.0  # In radians
        self.confidence = 0.0
        
    def update(self, scan):
        """
        Processes a new scan and estimates the rotation.
        Returns the estimated rotation angle (radians).
        """
        if self.last_scan is None:
            self.last_scan = scan
            return 0.0
        
        rotation = estimate_rotation_from_scans(self.last_scan, scan)
        
        if rotation is not None:
            self.estimated_heading = normalize_angle(self.estimated_heading + rotation)
            self.confidence = 0.9
            self.last_scan = scan
            return rotation
        else:
            # Tracking lost, confidence drops
            self.confidence *= 0.95
            return 0.0


def rotate_until_target(node, cmd_vel_pub, estimator, target_rotation_deg, tolerance_deg=5):
    """
    NAIVE algorithm to perform a rotation.
    
    Instead of turning "for X seconds", the robot turns until
    the LIDAR detects that the target angle has been reached.
    """
    target_rad = math.radians(target_rotation_deg)
    tolerance_rad = math.radians(tolerance_deg)
    
    start_heading = estimator.estimated_heading
    target_heading = normalize_angle(start_heading + target_rad)
    
    print(f"🔄 Naive rotation: target {target_rotation_deg}°")
    
    twist = Twist()
    twist.linear.x = 0.0
    twist.angular.z = 0.3 if target_rotation_deg > 0 else -0.3
    
    start_time = time.time()
    max_time = abs(target_rotation_deg) / 20.0 + 5.0  # Timeout
    
    while rclpy.ok() and (time.time() - start_time) < max_time:
        rclpy.spin_once(node, timeout_sec=0.05)
        
        # Check whether the target is reached
        current_diff = normalize_angle(estimator.estimated_heading - target_heading)
        
        if abs(current_diff) < tolerance_rad:
            print(f"✓ Rotation reached! Heading: {math.degrees(estimator.estimated_heading):.1f}°")
            break
        
        cmd_vel_pub.publish(twist)
        time.sleep(0.05)
    
    # Stop
    twist.linear.x = 0.0
    twist.angular.z = 0.0
    cmd_vel_pub.publish(twist)


def main():
    rclpy.init()
    node = rclpy.create_node('naive_rotation_mapper')
    
    cmd_vel_pub = node.create_publisher(Twist, '/cmd_vel', 10)
    
    estimator = NaiveRotationEstimator()
    
    def scan_cb(scan):
        rot = estimator.update(scan)
        if rot is not None:
            heading_deg = math.degrees(estimator.estimated_heading)
            print(f"  Rotation detected: {math.degrees(rot):+.1f}° | "
                  f"Heading: {heading_deg:.1f}° | Confidence: {estimator.confidence:.1%}")
    
    node.create_subscription(LaserScan, '/scan', scan_cb, qos_profile_sensor_data)
    
    print("""
    ╔════════════════════════════════════════╗
    │   NAÏVE LIDAR-BASED ROTATION MAPPER   │
    ╠════════════════════════════════════════╣
    │  Rotations are tracked with the LIDAR  │
    │  instead of the odometry.             │
    ╚════════════════════════════════════════╝
    """)
    
    try:
        # Let the LIDAR settle
        print("Calibration LIDAR...")
        for _ in range(20):
            rclpy.spin_once(node, timeout_sec=0.1)
            time.sleep(0.05)
        
        # TEST: perform a 90° rotation
        print("\n→ Rotation test 1: +90°")
        rotate_until_target(node, cmd_vel_pub, estimator, 90.0)
        time.sleep(1)
        
        print("\n← Rotation test 2: -180°")
        rotate_until_target(node, cmd_vel_pub, estimator, -180.0)
        time.sleep(1)
        
        print("\n→ Rotation test 3: +90° (back)")
        rotate_until_target(node, cmd_vel_pub, estimator, 90.0)
        
        print("\n✓ Tests finished")
        
    except KeyboardInterrupt:
        print("\nStopping...")
        twist = Twist()
        cmd_vel_pub.publish(twist)
    
    rclpy.shutdown()


if __name__ == '__main__':
    main()
