from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import LogInfo

def generate_launch_description():
    """
    Launch file that starts the LIDAR nodes
    Publisher: talker (LIDAR simulator)
    Subscriber: listener (LIDAR data processor)
    """
    
    return LaunchDescription([
        # Startup log
        LogInfo(msg="🚀 Starting the LIDAR nodes..."),
        
        # Node Publisher (LIDAR Publisher)
        Node(
            package='cpp_pubsub',
            executable='talker',
            name='lidar_publisher',
            output='screen',
        ),
        
        # Node Subscriber (LIDAR Subscriber)
        Node(
            package='cpp_pubsub',
            executable='listener',
            name='lidar_subscriber',
            output='screen',
        ),
        
        LogInfo(msg="✅ LIDAR nodes started - Topics: /scan, /data"),
    ])
