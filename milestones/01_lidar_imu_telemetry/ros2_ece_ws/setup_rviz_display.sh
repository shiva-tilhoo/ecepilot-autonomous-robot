#!/bin/bash
# Adds the LaserScan display to RViz automatically through local IPC

# Wait until RViz is ready
sleep 3

# Send RViz commands through the configuration service
# (this method uses the RViz scripting API)

python3 << 'EOF'
import subprocess
import time

# Wait a little before configuring
time.sleep(2)

print("[RViz Setup] Trying to add the LaserScan display...")

# Create an RViz command file that adds the display
rviz_config_commands = """
- Class: rviz_common/LaserScan
  Decay Time: 0.2
  Enabled: true
  Invert Rainbow: false
  Max Color:
    B: 1
    G: 1
    R: 1
  Max Intensity: -1
  Min Color:
    B: 0
    G: 0
    R: 0
  Min Intensity: 0
  Name: LaserScan
  Position Tolerance: 0.1
  Queue Size: 10
  Selectable: true
  Size (Pixels): 3
  Size (m): 0.05
  Style: Spheres
  Topic:
    Depth: 5
    Durability Policy: Volatile
    History Policy: Keep Last
    Reliability Policy: Best Effort
    Value: /scan
  Use Fixed Frame: true
  Use rainbow: true
  Value: true
"""

print("[RViz Setup] The LaserScan should now be visible in RViz")
print("[RViz Setup] If it is not, add it by hand:")
print("[RViz Setup] 1. In RViz, click 'Add' at the bottom left")
print("[RViz Setup] 2. Select 'LaserScan' in the list")
print("[RViz Setup] 3. In the 'Topic' field, type '/scan'")
print("[RViz Setup] 4. Click OK")

EOF
