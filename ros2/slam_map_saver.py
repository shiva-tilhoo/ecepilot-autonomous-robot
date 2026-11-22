#!/usr/bin/env python3
"""
Saves the SLAM map as a PNG for debugging/visualisation
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid
import numpy as np
from PIL import Image
import os
import time

class SlamMapSaver(Node):
    def __init__(self):
        super().__init__('slam_map_saver')
        
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )
        
        self.map_sub = self.create_subscription(
            OccupancyGrid, 
            '/map', 
            self.map_callback, 
            qos
        )
        
        self.last_save_time = 0
        self.save_interval = 2.0  # Save every 2 seconds
        self.output_path = os.path.join(os.getcwd(), 'slam_map_debug.png')
        self.frame_count = 0
        
        self.get_logger().info(f'🗺️  SLAM Map Saver started -> {self.output_path}')
        
    def map_callback(self, msg):
        """Converts the OccupancyGrid map to a PNG"""
        self.frame_count += 1
        current_time = time.time()
        
        # Debug: log reception (once per 5 callbacks)
        if self.frame_count % 5 == 0:
            self.get_logger().info(f'📍 Received /map message #{self.frame_count}: {msg.info.width}x{msg.info.height}px')
        
        # Save only once the interval has elapsed
        if current_time - self.last_save_time < self.save_interval:
            return
            
        try:
            self.last_save_time = current_time
            
            # Get the data
            width = msg.info.width
            height = msg.info.height
            data = np.array(msg.data, dtype=np.uint8).reshape((height, width))
            
            # Convert the occupancy grid (-1=unknown, 0=free, 100=occupied)
            # into an RGB image (0-255)
            img_array = np.zeros((height, width, 3), dtype=np.uint8)
            
            # White = free area (0)
            img_array[data == 0] = [255, 255, 255]
            
            # Black = occupied (100)
            img_array[data == 100] = [0, 0, 0]
            
            # Grey = unknown (-1)
            img_array[data == -1] = [128, 128, 128]
            
            # For the intermediate values (partially detected walls)
            mask_intermediate = (data > 0) & (data < 100)
            intermediate_val = (100 - data[mask_intermediate]) * 2.55
            img_array[mask_intermediate] = intermediate_val[:, np.newaxis]
            
            # Flip Y (ROS: origin at the bottom left, image: origin at the top left)
            img_array = np.flipud(img_array)
            
            # 🔲 AUTO-CROP: remove the empty borders (grey = unknown)
            # Find the bounds of the useful content (explored black or white)
            interesting_mask = (data != -1) & (data != 255)  # Everything except unknown
            
            if np.any(interesting_mask):
                # Find the rows/cols that hold content
                rows_with_content = np.any(interesting_mask, axis=1)
                cols_with_content = np.any(interesting_mask, axis=0)
                
                # Indices min/max
                ymin, ymax = np.where(rows_with_content)[0][[0, -1]]
                xmin, xmax = np.where(cols_with_content)[0][[0, -1]]
                
                # Add a small margin (10 pixels)
                margin = 10
                ymin = max(0, ymin - margin)
                ymax = min(height - 1, ymax + margin)
                xmin = max(0, xmin - margin)
                xmax = min(width - 1, xmax + margin)
                
                # Crop after the flip
                ymin_flip = height - 1 - ymax
                ymax_flip = height - 1 - ymin
                img_array = img_array[ymin_flip:ymax_flip+1, xmin:xmax+1]
            
            # Save
            img = Image.fromarray(img_array, 'RGB')
            img.save(self.output_path)
            
            # Log (new size after the crop)
            crop_h, crop_w = img_array.shape[:2]
            self.get_logger().info(
                f'✅ [#{self.frame_count}] Map saved: {width}x{height}px → cropped: {crop_w}x{crop_h}px '
                f'(resolution: {msg.info.resolution:.3f}m/px) '
                f'-> {self.output_path}'
            )
            
        except Exception as e:
            self.get_logger().error(f'❌ PNG save error: {e}')

def main():
    try:
        rclpy.init()
    except:
        pass
    
    node = SlamMapSaver()
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
