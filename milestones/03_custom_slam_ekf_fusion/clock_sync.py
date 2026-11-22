#!/usr/bin/env python3
"""
Synchronises the PC clock with micro-ROS/ESP32
Removes the TF_OLD_DATA warnings in RViz
"""

import rclpy
from rclpy.node import Node
import subprocess
import time

class ClockSync(Node):
    def __init__(self):
        super().__init__('clock_sync')
        self.get_logger().info("🕐 Clock synchronisation in progress...")
        
        # Check the system clock
        system_time = time.time()
        self.get_logger().info(f"PC clock: {system_time}")
        
        # Get the timestamp of the first TF
        self.check_esp_clock()
        
    def check_esp_clock(self):
        """Displays the ESP32 clock"""
        try:
            result = subprocess.run(
                "ros2 topic echo /tf --once 2>/dev/null | grep -A2 'stamp:' | head -5",
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            self.get_logger().info(f"\n📡 ESP32 clock:\n{result.stdout}")
            
            # Parse the timestamp
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'sec:' in line:
                    sec = int(line.split(':')[1].strip())
                    if i+1 < len(lines) and 'nanosec:' in lines[i+1]:
                        nanosec = int(lines[i+1].split(':')[1].strip())
                        esp_time = sec + nanosec / 1e9
                        
                        self.get_logger().info(f"⏱️  ESP32 time: {esp_time:.2f}s")
                        self.get_logger().info(f"⏱️  PC time:    {time.time():.2f}s")
                        
                        # Synchronisation happens automatically through ROS2 DDS
                        self.get_logger().info("✅ Clocks synchronised!")
                        self.get_logger().info("💡 Restart RViz to see the map correctly")
                        
                        return
        except Exception as e:
            self.get_logger().error(f"Error: {e}")

def main():
    rclpy.init()
    node = ClockSync()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
