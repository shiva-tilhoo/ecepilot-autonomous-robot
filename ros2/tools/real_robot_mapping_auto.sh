#!/bin/bash
# REAL_ROBOT_MAPPING_AUTO.SH - Start-up script of the complete system
# Starts every node of the autonomous mapping system in the right order

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/tmp/mapping_auto_logs"

# Create the logs folder
mkdir -p "$LOG_DIR"

echo "🚀 =========================================="
echo "🚀 REAL ROBOT AUTONOMOUS MAPPING SYSTEM"
echo "🚀 =========================================="
echo ""

# Cleanup function (Ctrl+C)
cleanup() {
    echo ""
    echo "⏹️  Stop detected (Ctrl+C)"
    echo "🔴 Shutting down every node..."
    
    # Kill every child process
    jobs -p | xargs -r kill -TERM 2>/dev/null || true
    sleep 1
    jobs -p | xargs -r kill -KILL 2>/dev/null || true
    
    echo "✅ Fully stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check that SLAM Toolbox is running
echo "⏳ Checking SLAM Toolbox..."
if ! timeout 2 ros2 topic list 2>/dev/null | grep -q "/map"; then
    echo "❌ ERROR: SLAM Toolbox does not seem to be running"
    echo "   Please start it first: ./start_robot_mapping_auto.sh"
    exit 1
fi
echo "✅ SLAM Toolbox detected"
echo ""

# Step 1: start wall_centering_node (autonomy)
echo "📍 Step 1/4: starting wall_centering_node (autonomy)..."
python3 "$SCRIPT_DIR/../wall_centering_node.py" \
    > "$LOG_DIR/wall_centering.log" 2>&1 &
WALL_PID=$!
sleep 2
echo "   ✅ PID: $WALL_PID"
echo ""

# Step 2: start loop_closure_detector
echo "📍 Step 2/4: starting loop_closure_detector (loop detection)..."
python3 "$SCRIPT_DIR/loop_closure_detector.py" \
    > "$LOG_DIR/loop_closure.log" 2>&1 &
LOOP_PID=$!
sleep 1
echo "   ✅ PID: $LOOP_PID"
echo ""

# Step 3: start trajectory_saver
echo "📍 Step 3/4: starting trajectory_saver (trajectory saving)..."
python3 "$SCRIPT_DIR/../trajectory_saver.py" \
    > "$LOG_DIR/trajectory_saver.log" 2>&1 &
SAVER_PID=$!
sleep 1
echo "   ✅ PID: $SAVER_PID"
echo ""

# Step 4: start return_path_generator
echo "📍 Step 4/4: starting return_path_generator (A* planning)..."
python3 "$SCRIPT_DIR/return_path_generator.py" \
    > "$LOG_DIR/return_path.log" 2>&1 &
RETURN_PID=$!
sleep 1
echo "   ✅ PID: $RETURN_PID"
echo ""

# Start the main orchestrator
echo "🎬 =========================================="
echo "🎬 Starting the main orchestrator..."
echo "🎬 =========================================="
echo ""

python3 "$SCRIPT_DIR/real_robot_mapping_auto.py"

# Wait for the end
wait

echo ""
echo "✅ System stopped cleanly"
