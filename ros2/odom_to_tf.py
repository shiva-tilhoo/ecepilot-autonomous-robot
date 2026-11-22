#!/usr/bin/env python3
"""
Publishes the odom -> base_link transform on TF2 from the Odometry messages
This bootstraps the TF chain for SLAM Toolbox
"""
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class OdomToTF(Node):
    def __init__(self):
        super().__init__('odom_to_tf')
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # QoS compatible with the bridge (BEST_EFFORT)
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.sub = self.create_subscription(Odometry, '/odom_ground_truth', self.odom_callback, qos)
        self.get_logger().info('✅ Odom -> TF publisher started (odom -> base_link)')

    def odom_callback(self, msg):
        # Build an odom -> base_link transform from the Odometry message
        tf = TransformStamped()
        tf.header.stamp = msg.header.stamp
        tf.header.frame_id = 'odom'
        tf.child_frame_id = 'base_link'
        
        tf.transform.translation.x = msg.pose.pose.position.x
        tf.transform.translation.y = msg.pose.pose.position.y
        tf.transform.translation.z = msg.pose.pose.position.z
        
        tf.transform.rotation = msg.pose.pose.orientation
        
        self.tf_broadcaster.sendTransform(tf)


def main():
    rclpy.init()
    node = OdomToTF()
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
