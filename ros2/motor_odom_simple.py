#!/usr/bin/env python3
"""
Motor Odometry Node - Init only
Only publishes a static odom -> base_link TF at the origin.
SLAM Toolbox does all the work through scan matching.
No motor logic, no cmd_vel, just the initial TF.
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy


class MotorOdomNode(Node):
    def __init__(self):
        super().__init__('motor_odom')

        self.declare_parameter('robot_frame', 'base_link')
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('publish_rate', 20.0)  # Hz

        self.robot_frame = self.get_parameter('robot_frame').value
        self.odom_frame  = self.get_parameter('odom_frame').value
        publish_rate     = float(self.get_parameter('publish_rate').value)

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.odom_pub      = self.create_publisher(Odometry, '/odom', qos)
        self.tf_broadcaster = TransformBroadcaster(self)

        period = 1.0 / publish_rate
        self.timer = self.create_timer(period, self._publish)

        self.get_logger().info(
            f'Motor Odom (init-only) started: {self.odom_frame} -> {self.robot_frame} @ {publish_rate}Hz'
        )

    def _publish(self):
        now = self.get_clock().now().to_msg()

        # TF odom -> base_link: fixed identity
        tf = TransformStamped()
        tf.header.stamp    = now
        tf.header.frame_id = self.odom_frame
        tf.child_frame_id  = self.robot_frame
        tf.transform.rotation.w = 1.0  # identity quaternion
        self.tf_broadcaster.sendTransform(tf)

        # /odom message: identity, very high covariance
        # SLAM Toolbox reads this as "I know nothing, trust the scan"
        odom = Odometry()
        odom.header.stamp    = now
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id  = self.robot_frame
        odom.pose.pose.orientation.w = 1.0

        # Huge covariance = SLAM ignores this odom and relies on the scan only
        BIG = 1e6
        odom.pose.covariance[0]  = BIG
        odom.pose.covariance[7]  = BIG
        odom.pose.covariance[35] = BIG
        odom.twist.covariance[0]  = BIG
        odom.twist.covariance[35] = BIG

        self.odom_pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = MotorOdomNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()