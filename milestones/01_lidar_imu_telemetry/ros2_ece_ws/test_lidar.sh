#!/bin/bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # directory of this script

# ============================================================
# Quick test script - ROS2 LIDAR PubSub
# ============================================================

set -e

WORKSPACE="$HERE"
PACKAGE="cpp_pubsub"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 Test ROS2 LIDAR Publisher/Subscriber${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

# Source ROS2
echo -e "${YELLOW}📦 Sourcing ROS2 environment...${NC}"
source "$WORKSPACE/install/setup.bash"

# Check the directories
if [ ! -d "$WORKSPACE" ]; then
    echo -e "${RED}✗ Workspace not found: $WORKSPACE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Workspace found${NC}\n"

# Function: test the publishers
test_publisher() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test 1: PUBLISHER (talker)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
    
    echo "Starting the publisher for 5 seconds..."
    echo "Stop with: Ctrl+C\n"
    
    sleep 2
    
    timeout 5 ros2 run $PACKAGE talker || true
    
    echo -e "\n${GREEN}✓ Publisher test finished${NC}\n"
}

# Function: test the subscribers
test_subscriber() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test 2: SUBSCRIBER (listener)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
    
    echo "Note: start the publisher in another terminal first!"
    echo "Then run this test.\n"
    
    timeout 10 ros2 run $PACKAGE listener || true
    
    echo -e "\n${GREEN}✓ Subscriber test finished${NC}\n"
}

# Function: test the topics
test_topics() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test 3: ROS2 TOPICS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
    
    echo -e "${YELLOW}Available topics:${NC}"
    ros2 topic list || true
    
    echo ""
    echo -e "${YELLOW}Info on /scan:${NC}"
    ros2 topic info /scan || true
    
    echo ""
    echo -e "${YELLOW}Info on /data:${NC}"
    ros2 topic info /data || true
    
    echo -e "\n${GREEN}✓ Topics test finished${NC}\n"
}

# Function: test the launch file
test_launch() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test 4: LAUNCH FILE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
    
    echo "Starting the launch file for 10 seconds..."
    echo "Stop with: Ctrl+C\n"
    
    sleep 2
    
    timeout 10 ros2 launch $PACKAGE lidar_launch.py || true
    
    echo -e "\n${GREEN}✓ Launch file test finished${NC}\n"
}

# Function: full system test
test_full_system() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Test 5: FULL SYSTEM (Publisher + Subscriber)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
    
    echo -e "${YELLOW}Starting the full system...${NC}\n"
    
    # Start the publisher in the background
    ros2 run $PACKAGE talker &
    PUB_PID=$!
    
    sleep 2
    
    # Start the subscriber (5 seconds)
    timeout 5 ros2 run $PACKAGE listener || true
    
    # Kill the publisher
    kill $PUB_PID 2>/dev/null || true
    
    echo -e "\n${GREEN}✓ Full system test finished${NC}\n"
}

# Menu
case $1 in
    1|publisher)
        test_publisher
        ;;
    2|subscriber)
        test_subscriber
        ;;
    3|topics)
        test_topics
        ;;
    4|launch)
        test_launch
        ;;
    5|full)
        test_full_system
        ;;
    all)
        echo -e "${YELLOW}Running every test...${NC}\n"
        test_publisher
        echo "Press Enter to continue..."
        read
        test_topics
        test_launch
        ;;
    *)
        cat << EOF
${BLUE}Usage: $0 [TEST]${NC}

Available tests:
  ${GREEN}1, publisher${NC}    Test the Publisher
  ${GREEN}2, subscriber${NC}   Test the Subscriber
  ${GREEN}3, topics${NC}       Test the ROS2 topics
  ${GREEN}4, launch${NC}       Test the launch file
  ${GREEN}5, full${NC}        Test the full system
  ${GREEN}all${NC}            Run every test

Examples:
  $0 publisher
  $0 launch
  $0 all

EOF
        exit 0
        ;;
esac

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Tests finished successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
