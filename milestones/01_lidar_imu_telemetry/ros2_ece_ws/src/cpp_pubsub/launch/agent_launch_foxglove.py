import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import LogInfo, TimerAction, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    """
    Launch file for the micro_ros agent + Foxglove Studio with the REAL ESP32 LIDAR
    Shows all 360 LIDAR points live in Foxglove
    Includes the 3D model of the car
    """
    
    # Get vehicle description package directory
    vehicle_description_dir = get_package_share_directory('vehicle_description')
    vehicle_launch = os.path.join(
        vehicle_description_dir, 'launch', 'vehicle_broadcaster.launch.py'
    )
    
    # Delay before starting Foxglove (gives the topics time to appear)
    foxglove_delayed = TimerAction(
        period=3.0,  # 3-second delay
        actions=[
            ExecuteProcess(
                cmd=['foxglove-studio'],
                output='screen',
            ),
        ]
    )
    
    return LaunchDescription([
        LogInfo(msg="\n" + "="*70),
        LogInfo(msg="[LAUNCH] ESP32 LIDAR - Micro ROS Agent setup + 3D CAR (Foxglove)"),
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
        
        # ==================== FOXGLOVE VISUALIZER (delayed) ====================
        foxglove_delayed,
        
        LogInfo(msg="\n[OK] Listener started - Foxglove Studio will start in 3 seconds\n"),
        LogInfo(msg="[CONFIG] REQUIRED SETUP:"),
        LogInfo(msg="   Start the micro_ros agent in ANOTHER terminal:"),
        LogInfo(msg="   "),
        LogInfo(msg="   docker run -it --rm microros/micro-ros-docker:humble \\"),
        LogInfo(msg="     ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888"),
        LogInfo(msg="   "),
        LogInfo(msg="[TOPICS] TOPICS RECEIVED FROM THE ESP32:"),
        LogInfo(msg="   - /scan (sensor_msgs/LaserScan) - 360 LIDAR points"),
        LogInfo(msg="   - /data (std_msgs/Int32) - Counter"),
        LogInfo(msg="   - /scan_cloud (sensor_msgs/PointCloud2) - 3D points"),
        LogInfo(msg=""),
        LogInfo(msg="[VISUAL] FOXGLOVE VISUALISATION (3D):"),
        LogInfo(msg="   - Modern, intuitive web interface"),
        LogInfo(msg="   - 3D model of the car in the centre"),
        LogInfo(msg="   - LIDAR points displayed live"),
        LogInfo(msg="   - Left panel to select the topics to display"),
        LogInfo(msg="   - Display of the /data counter"),
        LogInfo(msg=""),
        LogInfo(msg="[TIPS] FOXGLOVE STUDIO:"),
        LogInfo(msg="   1. Click 'Add panel' (top right)"),
        LogInfo(msg="   2. Select '3D' for the 3D view"),
        LogInfo(msg="   3. Select '/scan_cloud' in the topic list"),
        LogInfo(msg="   4. Use the 'Telemetry' panel to see the values"),
        LogInfo(msg="   5. Navigate with the mouse: scroll=zoom, right-click=rotate"),
        LogInfo(msg="   6. Use 'Time scrubbing' to replay the history"),
        LogInfo(msg="\n" + "="*70 + "\n"),
    ])
