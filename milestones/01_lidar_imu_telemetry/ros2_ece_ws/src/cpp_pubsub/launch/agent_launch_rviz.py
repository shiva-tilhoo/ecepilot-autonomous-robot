import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import LogInfo, TimerAction, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """
    Launch file for the micro_ros agent + RViz with the REAL ESP32 LIDAR
    Shows all 360 LIDAR points live
    Includes the 3D model of the car
    """
    
    # Get vehicle description package directory
    vehicle_description_dir = get_package_share_directory('vehicle_description')
    vehicle_launch = os.path.join(
        vehicle_description_dir, 'launch', 'vehicle_broadcaster.launch.py'
    )
    
    # Path to the RViz config (optimised 3D view)
    rviz_config = os.path.join(
        os.path.dirname(__file__),
        'lidar_buffer.rviz'  # Use the RViz config made for PointCloud2
    )
    
    # Delay before starting RViz (gives the topics time to appear)
    rviz_delayed = TimerAction(
        period=5.0,  # 5-second delay
        actions=[
            ExecuteProcess(
                cmd=['rviz2', '-d', rviz_config],
                output='screen',
            ),
        ]
    )
    
    return LaunchDescription([
        LogInfo(msg="\n" + "="*70),
        LogInfo(msg="[LAUNCH] ESP32 LIDAR - Micro ROS Agent setup + 3D CAR (RViz)"),
        LogInfo(msg="="*70 + "\n"),
        
        # ==================== VEHICLE DESCRIPTION (3D model of the car) ====================
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(vehicle_launch),
            launch_arguments={}.items(),
        ),
        
        # ==================== TF BROADCASTER (publishes the lidar_link frame) ====================
        Node(
            package='cpp_pubsub',
            executable='tf_broadcaster',
            name='tf_broadcaster',
            output='screen',
        ),
        
        # ==================== LIDAR BUFFER (accumulates the scans) ====================
        Node(
            package='cpp_pubsub',
            executable='lidar_buffer',
            name='lidar_buffer',
            output='screen',
            parameters=[
                {'buffer_size': 20},  # Keeps 20 scans (clears faster)
            ],
        ),
        
        # ==================== LISTENER (receives and logs the data) ====================
        Node(
            package='cpp_pubsub',
            executable='listener',
            name='lidar_subscriber',
            output='screen',
        ),
        
        # ==================== RVIZ VISUALIZER (delayed) ====================
        rviz_delayed,
        
        LogInfo(msg="\n[OK] Listener started - RViz will start in 5 seconds\n"),
        LogInfo(msg="[CONFIG] REQUIRED SETUP:"),
        LogInfo(msg="   Start the micro_ros agent in ANOTHER terminal:"),
        LogInfo(msg="   "),
        LogInfo(msg="   docker run -it --rm microros/micro-ros-docker:humble \\"),
        LogInfo(msg="     ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888"),
        LogInfo(msg="   "),
        LogInfo(msg="[TOPICS] TOPICS RECEIVED FROM THE ESP32:"),
        LogInfo(msg="   - /scan (sensor_msgs/LaserScan) - 360 LIDAR points"),
        LogInfo(msg="   - /data (std_msgs/Int32) - Counter"),
        LogInfo(msg=""),
        LogInfo(msg="[VISUAL] RVIZ VISUALISATION (3D):"),
        LogInfo(msg="   - 3D model of the car in the centre"),
        LogInfo(msg="   - LIDAR points in red around the vehicle"),
        LogInfo(msg="   - Blue box = vehicle base"),
        LogInfo(msg="   - Red cylinder = LIDAR on the roof"),
        LogInfo(msg="   - Black cylinders = wheels"),
        LogInfo(msg="   - XY grid for spatial orientation"),
        LogInfo(msg="   - Frame: base_link (centre of the car)"),
        LogInfo(msg=""),
        LogInfo(msg="[TIPS] RVIZ TIPS:"),
        LogInfo(msg="   - Use the 'Displays' panel to enable/disable LaserScan"),
        LogInfo(msg="   - Scroll to zoom, right-click to rotate the view"),
        LogInfo(msg="   - Increase 'Decay Time' to see the history"),
        LogInfo(msg="   - Change the colour with 'Color Transformer'"),
        LogInfo(msg="\n" + "="*70 + "\n"),
    ])
