#!/bin/bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # directory of this script

###############################################################################
# SETUP GUIDE - ECE ROS2 + microROS Project
# 
# This script installs all dependencies for the project
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check OS
if [[ ! "$OSTYPE" == "linux-gnu"* ]]; then
    print_error "This script is designed for Linux. Please run it on Ubuntu 22.04+"
    exit 1
fi

print_header "ECE ROS2 + microROS Setup"

# Update system
print_info "Updating the system..."
sudo apt update
sudo apt upgrade -y

# Install ROS2 Humble
print_header "Installing ROS2 Humble"

if [ ! -d "/opt/ros/humble" ]; then
    print_info "Adding the ROS2 repository..."
    sudo apt install software-properties-common -y
    sudo add-apt-repository universe -y
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    
    sudo apt update
    print_info "Installing ROS2 Humble (this can take a few minutes)..."
    sudo apt install ros-humble-desktop -y
    print_success "ROS2 Humble installed"
else
    print_success "ROS2 Humble already installed"
fi

# Install colcon
print_header "Installation Colcon"
print_info "Installing colcon..."
sudo apt install python3-colcon-common-extensions -y
print_success "Colcon installed"

# Install RViz2
print_header "Installation RViz2"
sudo apt install ros-humble-rviz2 -y
print_success "RViz2 installed"

# Install PlatformIO
print_header "Installation PlatformIO"
if ! command -v platformio &> /dev/null; then
    print_info "Installing PlatformIO..."
    pip install platformio
    print_success "PlatformIO installed"
else
    print_success "PlatformIO already installed"
fi

# Install Docker
print_header "Installation Docker"
if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_success "Docker installed"
    print_info "⚠️  Log out and back in for the docker permissions to take effect"
else
    print_success "Docker already installed"
fi

# Pull microROS Docker image
print_header "Image Docker microROS"
print_info "Downloading the microROS image..."
docker pull microros/micro-ros-docker:humble
print_success "microROS image downloaded"

# Install Python dependencies
print_header "Python dependencies"
print_info "Installing the Python dependencies..."
pip install numpy matplotlib pygame
print_success "Python dependencies installed"

# Create sourcing script
print_header "Configuration script"
cat > ~/.bashrc_ros2_ece << EOF
# ECE ROS2 + microROS Setup

# ROS2 Humble
source /opt/ros/humble/setup.bash

# Workspace
if [ -f "$HERE/ros2_ece_ws/install/setup.bash" ]; then
    source "$HERE/ros2_ece_ws/install/setup.bash"
fi

# Aliases
alias build_ros2='cd "$HERE/ros2_ece_ws" && colcon build && source install/setup.bash'
alias run_lidar='cd "$HERE/ros2_ece_ws" && ros2 run cpp_pubsub listener'
alias run_rviz='cd "$HERE/ros2_ece_ws" && ros2 launch rviz2 rviz2 -d lidar_config.rviz'
alias run_agent='docker run -it --rm microros/micro-ros-docker:humble ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888'
alias build_pio='cd "$HERE/firmware" && platformio run'
alias upload_pio='cd "$HERE/firmware" && platformio run --target upload'
EOF

# Add to bashrc
if ! grep -q "ros2_ece" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Load ECE ROS2 configuration" >> ~/.bashrc
    echo "if [ -f ~/.bashrc_ros2_ece ]; then" >> ~/.bashrc
    echo "    source ~/.bashrc_ros2_ece" >> ~/.bashrc
    echo "fi" >> ~/.bashrc
fi

print_success "Configuration script created"

# Build workspace
print_header "Building the ROS2 workspace"
print_info "This can take 5-10 minutes..."
cd "$HERE/ros2_ece_ws"
source /opt/ros/humble/setup.bash
colcon build --event-handlers console_direct+
print_success "Workspace built"

# Summary
print_header "Installation complete! ✓"
echo ""
echo "Check your installation:"
echo ""
print_info "Source the ROS2 configuration:"
echo "  source ~/.bashrc_ros2_ece"
echo ""
print_info "Or use the aliases that were created:"
echo "  build_ros2    - Build the ROS2 workspace"
echo "  run_lidar     - Start the LIDAR listener"
echo "  run_rviz      - Start RViz"
echo "  run_agent     - Start the microROS agent"
echo "  build_pio     - Build the PlatformIO firmware"
echo "  upload_pio    - Flash the ESP32"
echo ""
print_info "Test commands:"
echo "  ros2 --version"
echo "  platformio --version"
echo "  docker --version"
echo ""
print_info "Next steps:"
echo "  1. Log out and back in (for the Docker permissions)"
echo "  2. Open a new terminal"
echo "  3. Run: source ~/.bashrc_ros2_ece"
echo "  4. Follow QUICKSTART.md to start the project"
echo ""

print_success "Installation ready! Happy hacking! 🚀"
