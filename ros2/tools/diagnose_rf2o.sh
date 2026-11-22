#!/bin/bash
# Diagnostic script that checks whether RF2O can see the LIDAR data

echo "=========================================="
echo "RF2O + SIMULATED LIDAR STACK DIAGNOSTIC"
echo "=========================================="
echo ""

echo "1️⃣ Checking the ROS 2 topics..."
echo "--- Available topics ---"
ros2 topic list 2>/dev/null || echo "❌ ROS 2 not initialised"

echo ""
echo "2️⃣ Checking the /scan_raw topic..."
if ros2 topic list 2>/dev/null | grep -q "scan_raw"; then
    echo "✅ /scan_raw exists"
    echo "--- Topic info ---"
    ros2 topic info /scan_raw
else
    echo "❌ /scan_raw does not exist!"
fi

echo ""
echo "3️⃣ Checking the /scan topic..."
if ros2 topic list 2>/dev/null | grep -q "^/scan$"; then
    echo "✅ /scan exists"
    echo "--- Topic info ---"
    ros2 topic info /scan
else
    echo "❌ /scan does not exist!"
fi

echo ""
echo "4️⃣ Checking the /odom topic..."
if ros2 topic list 2>/dev/null | grep -q "^/odom$"; then
    echo "✅ /odom exists (RF2O is publishing)"
    echo "--- Topic info ---"
    ros2 topic info /odom
else
    echo "❌ /odom does not exist! RF2O is not publishing"
fi

echo ""
echo "5️⃣ Checking the TF..."
ros2 tf2_py tf_echo base_link laser_link 2>/dev/null && echo "✅ Transform base_link -> laser_link OK" || echo "❌ Transform manquante"

echo ""
echo "6️⃣ Diagnostic RF2O..."
ps aux | grep rf2o_laser_odometry | grep -v grep && echo "✅ RF2O node is running" || echo "❌ RF2O node is not running"

echo ""
echo "=========================================="
echo "End of the diagnostic"
echo "=========================================="
