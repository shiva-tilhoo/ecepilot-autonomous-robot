#!/bin/bash
# Debug version of the start-up with detailed logs

echo "=========================================="
echo "FULL DEBUG START-UP: LIDAR + RF2O"
echo "=========================================="

# --- Thorough cleanup ---
echo "🧹 Cleaning up the previous processes..."
pkill -9 rf2o 2>/dev/null || true
pkill -9 slam_toolbox 2>/dev/null || true
pkill -9 static_transform_publisher 2>/dev/null || true
pkill -9 scan_restamper 2>/dev/null || true
pkill -9 simu_lidar 2>/dev/null || true
pkill -9 simu_bridge 2>/dev/null || true
sleep 2

# --- Start-up with logs ---
echo ""
echo "1️⃣ Starting the LIDAR SIMULATOR (simu_lidar.py)..."
python3 simu_lidar.py 2>&1 | sed 's/^/[SIMU_LIDAR] /' &
sleep 2

echo "✅ Simulator started"

echo ""
echo "2️⃣ Starting the SOCKET->ROS2 BRIDGE (simu_bridge.py)..."
python3 simu_bridge.py 2>&1 | sed 's/^/[SIMU_BRIDGE] /' &
sleep 1

echo "✅ Bridge started"

echo ""
echo "3️⃣ Starting the TF2 PUBLISHER..."
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link laser_link 2>&1 | sed 's/^/[TF2] /' &

echo "✅ TF2 started"

echo ""
echo "4️⃣ Starting the RESTAMPER (scan_restamper_simu.py)..."
python3 scan_restamper_simu.py 2>&1 | sed 's/^/[RESTAMPER] /' &
sleep 1

echo "✅ Restamper started"

echo ""
echo "5️⃣ Starting the TEST LISTENER..."
python3 test_rf2o_lidar.py 2>&1 | sed 's/^/[TEST_LISTENER] /' &
sleep 1

echo "✅ Test listener started"

echo ""
echo "=========================================="
echo "All components are running!"
echo "=========================================="
echo ""

echo "Visible topics (in 3 seconds):"
sleep 3
ros2 topic list

echo ""
echo "RF2O can be enabled in 5 seconds..."
echo "Once everything is ✅, RF2O can be configured"
sleep 5

echo ""
echo "=========================================="
echo "⏸️ Stack ready - RF2O ready to be started"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  ros2 topic echo /scan_raw   # Shows the raw scans"
echo "  ros2 topic echo /scan       # Shows the re-stamped scans"
echo "  ros2 topic echo /odom       # Shows the RF2O odometry"
echo "  ./diagnose_rf2o.sh          # Diagnostic complet"
echo ""

# Keep the script running
wait
