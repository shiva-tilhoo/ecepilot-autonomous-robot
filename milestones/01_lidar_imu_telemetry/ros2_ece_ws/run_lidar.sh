#!/bin/bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # directory of this script

# ============================================================
# Helper script to start the complete LIDAR system
# ============================================================

set -e

WORKSPACE_PATH="$HERE"
PACKAGE="cpp_pubsub"

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Checks
check_requirements() {
    print_header "🔍 Checking dependencies"
    
    if ! command -v colcon &> /dev/null; then
        print_error "colcon not installed"
        echo "Install with: sudo apt install python3-colcon-common-extensions"
        exit 1
    fi
    print_success "colcon installed"
    
    if ! command -v ros2 &> /dev/null; then
        print_error "ROS2 not found"
        echo "Make sure you sourced install/setup.bash"
        exit 1
    fi
    print_success "ROS2 found"
    
    if [ ! -d "$WORKSPACE_PATH" ]; then
        print_error "Workspace not found: $WORKSPACE_PATH"
        exit 1
    fi
    print_success "Workspace found"
}

# Build
build_package() {
    print_header "🔨 Building the package"
    
    cd "$WORKSPACE_PATH"
    
    if colcon build --packages-select $PACKAGE 2>&1 | grep -i error; then
        print_error "Build failed"
        exit 1
    fi
    
    print_success "Package built successfully"
}

# Source
source_setup() {
    print_header "📦 Setting up the environment"
    
    source "$WORKSPACE_PATH/install/setup.bash"
    print_success "Environment ready"
}

# Start the system
run_system() {
    local mode=$1
    
    print_header "🚀 Starting the system"
    
    case $mode in
        publisher)
            print_warning "Starting the Publisher only"
            ros2 run $PACKAGE talker
            ;;
        subscriber)
            print_warning "Starting the Subscriber only"
            ros2 run $PACKAGE listener
            ;;
        both)
            print_warning "Starting the Publisher and the Subscriber"
            echo "Note: open 2 separate terminals:"
            echo "  Terminal 1: ros2 run $PACKAGE talker"
            echo "  Terminal 2: ros2 run $PACKAGE listener"
            ;;
        launch)
            print_warning "Starting with the launch file"
            ros2 launch $PACKAGE lidar_launch.py
            ;;
        launch-complete)
            print_warning "Full start (Publisher + Subscriber + RViz)"
            ros2 launch $PACKAGE lidar_complete_launch.py
            ;;
        agent)
            print_warning "Starting with the micro_ros agent"
            ros2 launch $PACKAGE agent_launch.py
            ;;
        monitor)
            print_warning "Monitoring the topics"
            echo "Available topics:"
            ros2 topic list
            echo ""
            echo "Topic rates:"
            for topic in /scan /data; do
                if ros2 topic list | grep -q $topic; then
                    echo "  $topic: $(ros2 topic hz $topic --window 3 2>/dev/null | tail -1)"
                fi
            done
            ;;
        *)
            print_error "Mode inconnu: $mode"
            print_usage
            exit 1
            ;;
    esac
}

# Show the help
print_usage() {
    cat << EOF
${BLUE}Usage: $0 [OPTION]${NC}

Options:
    ${GREEN}publisher${NC}       Start the Publisher only
    ${GREEN}subscriber${NC}      Start the Subscriber only
    ${GREEN}both${NC}           Show the commands for both nodes
    ${GREEN}launch${NC}         Start with the launch file (Publisher + Subscriber)
    ${GREEN}launch-complete${NC} Full start (Publisher + Subscriber + RViz)
    ${GREEN}agent${NC}          Start to receive data from the ESP32 agent
    ${GREEN}monitor${NC}        Monitor the ROS2 topics
    ${GREEN}build${NC}          Build the package only
    ${GREEN}clean${NC}          Clean the build
    ${GREEN}-h, --help${NC}      Show this help

Examples:
    $0 launch              # Simple start
    $0 publisher           # Start the publisher
    $0 monitor             # Show the active topics

Topics ROS2:
    /scan                  LaserScan (LIDAR data)
    /data                  Int32 (counter)

Important files:
    Launch files: $WORKSPACE_PATH/src/$PACKAGE/launch/
    Package config: $WORKSPACE_PATH/src/$PACKAGE/CMakeLists.txt
    README: $WORKSPACE_PATH/src/$PACKAGE/README.md
EOF
}

# Main
main() {
    if [ $# -eq 0 ]; then
        print_usage
        exit 0
    fi
    
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        build)
            check_requirements
            build_package
            exit 0
            ;;
        clean)
            print_header "🧹 Cleaning"
            cd "$WORKSPACE_PATH"
            rm -rf build install log
            print_success "Clean finished"
            exit 0
            ;;
        *)
            check_requirements
            build_package
            source_setup
            run_system "$1"
            ;;
    esac
}

# Execution
main "$@"
