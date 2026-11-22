#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import LaserScan

class ScanRestamperSimu(Node):
    def __init__(self):
        super().__init__('scan_restamper_simu')
        # Uses BEST_EFFORT for better compatibility
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.sub = self.create_subscription(LaserScan, '/scan_raw', self.callback, qos)
        self.pub = self.create_publisher(LaserScan, '/scan', qos)
        self.scan_count = 0
        self.target_hz = 15.0
        self.min_period_ns = int(1e9 / self.target_hz)
        self.last_pub_ns = 0
        self.get_logger().info('✅ Restamper started - Input: /scan_raw -> Output: /scan')

    def callback(self, msg):
        now_ns = self.get_clock().now().nanoseconds
        if self.last_pub_ns and (now_ns - self.last_pub_ns) < self.min_period_ns:
            return
        self.last_pub_ns = now_ns

        # Update the timestamp with the current ROS clock
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "laser_link"
        self.pub.publish(msg)
        self.scan_count += 1
        if self.scan_count % 30 == 0:
            self.get_logger().info(f'✅ {self.scan_count} scans processed, {len(msg.ranges)} rays per scan')

def main():
    try:
        rclpy.init()
    except:
        pass
    
    node = ScanRestamperSimu()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()