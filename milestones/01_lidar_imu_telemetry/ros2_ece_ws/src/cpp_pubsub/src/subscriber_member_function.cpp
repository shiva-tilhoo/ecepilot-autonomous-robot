#include <memory>
#include <cmath>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/int32.hpp"

using std::placeholders::_1;
class MinimalSubscriber : public rclcpp::Node
{
public:
  MinimalSubscriber()
  : Node("lidar_subscriber"), scan_count_(0), counter_count_(0)
  {
    // Subscriber for LaserScan
    scan_subscription_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan", 10, std::bind(&MinimalSubscriber::scan_callback, this, _1));
    
    // Subscriber for Counter
    counter_subscription_ = this->create_subscription<std_msgs::msg::Int32>(
      "/data", 10, std::bind(&MinimalSubscriber::counter_callback, this, _1));
    
    RCLCPP_INFO(this->get_logger(), "LIDAR Subscriber started - Topics: /scan, /data");
  }

private:
  void counter_callback(const std_msgs::msg::Int32::SharedPtr msg) const
  {
    RCLCPP_INFO(this->get_logger(), "📊 Counter received: %d", msg->data);
  }

  void scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg)
  {
    scan_count_++;
    
    // Print the general scan info
    RCLCPP_INFO(this->get_logger(), 
      "\n════════════════════════════════════════════\n"
      "🔍 LIDAR SCAN #%zu received\n"
      "Frame ID: %s\n"
      "Number of points: %zu\n"
      "Angle Min/Max: %.2f / %.2f rad (%.1f° / %.1f°)\n"
      "Angle Increment: %.4f rad (%.2f°)\n"
      "Range Min/Max: %.2f / %.2f m\n"
      "════════════════════════════════════════════",
      scan_count_,
      msg->header.frame_id.c_str(),
      msg->ranges.size(),
      msg->angle_min, msg->angle_max,
      msg->angle_min * 180.0f / M_PI, msg->angle_max * 180.0f / M_PI,
      msg->angle_increment,
      msg->angle_increment * 180.0f / M_PI,
      msg->range_min, msg->range_max);
    
    // Find the closest obstacle
    float closest_range = msg->range_max + 1.0f;
    int closest_idx = -1;
    float front_min_distance = msg->range_max + 1.0f;
    int front_min_idx = -1;
    
    for(size_t i = 0; i < msg->ranges.size(); ++i)
    {
      float r = msg->ranges[i];
      
      // Find the global minimum
      if(r < closest_range && r >= msg->range_min && r <= msg->range_max)
      {
        closest_range = r;
        closest_idx = i;
      }
      
      // Find the minimum ahead (±15° around 0°)
      float angle_deg = i * msg->angle_increment * 180.0f / M_PI;
      if(angle_deg > 345.0f || angle_deg < 15.0f)  // Front cone ±15°
      {
        if(r < front_min_distance && r >= msg->range_min && r <= msg->range_max)
        {
          front_min_distance = r;
          front_min_idx = i;
        }
      }
    }
    
    // Print the results
    if(closest_idx >= 0)
    {
      float angle = closest_idx * msg->angle_increment;
      float angle_deg = angle * 180.0f / M_PI;
      RCLCPP_WARN(this->get_logger(),
        "⚠️  Closest obstacle: %.2f m @ index %d (angle: %.1f°)",
        closest_range, closest_idx, angle_deg);
    }
    
    if(front_min_idx >= 0 && front_min_distance < 1.0f)
    {
      float angle = front_min_idx * msg->angle_increment;
      float angle_deg = angle * 180.0f / M_PI;
      RCLCPP_ERROR(this->get_logger(),
        "🚨 DANGER! Obstacle ahead: %.2f m @ %.1f° (too close!)",
        front_min_distance, angle_deg);
    }
    
    // Print the distance statistics
    float avg_distance = 0.0f;
    int valid_points = 0;
    
    for(size_t i = 0; i < msg->ranges.size(); ++i)
    {
      if(msg->ranges[i] >= msg->range_min && msg->ranges[i] <= msg->range_max)
      {
        avg_distance += msg->ranges[i];
        valid_points++;
      }
    }
    
    if(valid_points > 0)
    {
      avg_distance /= valid_points;
      RCLCPP_INFO(this->get_logger(),
        "📈 Statistics - Valid points: %d / %zu, Mean distance: %.2f m",
        valid_points, msg->ranges.size(), avg_distance);
    }
    
    // Print the first 5 points (for debugging)
    if(msg->ranges.size() > 0)
    {
      RCLCPP_DEBUG(this->get_logger(), "First LIDAR points:");
      for(size_t i = 0; i < std::min(size_t(5), msg->ranges.size()); ++i)
      {
        RCLCPP_DEBUG(this->get_logger(),
          "  Point %zu: distance=%.3f m, intensity=%.1f",
          i, msg->ranges[i], 
          i < msg->intensities.size() ? msg->intensities[i] : 0.0f);
      }
    }
  }

  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_subscription_;
  rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr counter_subscription_;
  mutable size_t scan_count_;
  mutable size_t counter_count_;
};
int main(int argc, char * argv[])
{
rclcpp::init(argc, argv);
rclcpp::spin(std::make_shared<MinimalSubscriber>());
rclcpp::shutdown();
return 0;
}