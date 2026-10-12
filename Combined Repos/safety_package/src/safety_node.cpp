/**
 * @file safety_node.cpp
 * @brief Automatic emergency braking node based on LiDAR time-to-collision (TTC).
 *
 * C++ implementation of safety_package/safety_node.py. Both nodes use the same
 * node name, topics, parameters and logic, so only one of them should run at a time.
 */
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <functional>
#include <limits>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "ackermann_msgs/msg/ackermann_drive_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

using namespace std::chrono_literals;

/**
 * @brief The class that handles emergency braking based on LiDAR data.
 *
 * The node drives the car forward at a fixed cruise speed and stops it when
 * the time-to-collision (TTC) with any obstacle ahead becomes too small.
 *
 * Data flow:
 *   - /odom -> odom_callback        -> stores the current speed
 *   - /scan -> scan_callback        -> computes TTC, latches/releases the brake
 *   - timer -> drive_timer_callback -> publishes the drive command at 50Hz
 *
 * Parameters:
 *   - ttc_threshold (double): Brake when the TTC drops below this, in seconds.
 *   - release_distance (double): Distance in metres the front cone must be
 *     clear before a latched brake is released.
 *   - release_cone_angle (double): Half-width in degrees of the front cone
 *     checked for release.
 *   - sensor_timeout (double): Brake if /scan or /odom is older than this,
 *     in seconds.
 *   - cruise_speed (double): Speed in m/s commanded while the path is clear.
 */
class SafetyNode : public rclcpp::Node
{
public:
  /**
   * @brief Set up the node parameters, subscribers, publisher and timer.
   */
  SafetyNode()
  : Node("safety_node")
  {
    // Parameters
    declare_parameter("ttc_threshold", 0.5);        // Brake when TTC drops below this (s)
    declare_parameter("release_distance", 1.0);     // Front must be clear this far (m) to release
    declare_parameter("release_cone_angle", 20.0);  // Half-width of the release cone (deg)
    declare_parameter("sensor_timeout", 0.25);      // Brake if /scan or /odom is older (s)
    declare_parameter("cruise_speed", 1.0);         // Speed commanded while path is clear (m/s)

    // Subscribers
    odom_subscriber_ = create_subscription<nav_msgs::msg::Odometry>(
      "/odom",
      rclcpp::SensorDataQoS(),
      std::bind(&SafetyNode::odom_callback, this, std::placeholders::_1));

    scan_subscriber_ = create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan",
      rclcpp::SensorDataQoS(),
      std::bind(&SafetyNode::scan_callback, this, std::placeholders::_1));

    // Publisher
    drive_publisher_ = create_publisher<ackermann_msgs::msg::AckermannDriveStamped>(
      "/drive",
      10);

    // Timer (50Hz publishing)
    drive_timer_ = create_wall_timer(
      20ms,
      std::bind(&SafetyNode::drive_timer_callback, this));
  }

private:
  /// Below this speed (m/s) the car is considered stopped.
  static constexpr double kMinSpeedThreshold = 0.05;
  /// Below this closing speed (m/s) a beam cannot collide (avoids divide by zero).
  static constexpr double kMinClosingSpeed = 1e-3;

  /**
   * @brief Store the car's current speed from an odometry message.
   *
   * Also records the arrival time so the watchdog in drive_timer_callback()
   * can tell that odometry is still fresh.
   *
   * @param odom_msg Latest odometry; the speed is read from
   *        twist.twist.linear.x in m/s.
   */
  void odom_callback(const nav_msgs::msg::Odometry::ConstSharedPtr odom_msg)
  {
    speed_ = odom_msg->twist.twist.linear.x;
    last_odom_time_ = now();
    RCLCPP_INFO(get_logger(), "🛑 Current Speed: %.2f m/s", speed_);
  }

  /**
   * @brief Compute the time-to-collision (TTC) from a LiDAR scan and update the brake.
   *
   * For every valid beam the closing speed is `speed * cos(angle)` and the
   * TTC is `range / closing speed`. The smallest TTC over all beams decides
   * the brake state:
   *
   *   - Latch: the brake is set, and a stop command published immediately,
   *     when the smallest TTC falls below `ttc_threshold`.
   *   - Release: a latched brake is cleared only once the car has stopped
   *     and the nearest obstacle in the front cone is farther than
   *     `release_distance`. TTC cannot be used here because it is infinite
   *     when the car is not moving.
   *
   * @param scan_msg Latest LiDAR scan. Angle 0 is straight ahead; ranges are
   *        in metres.
   */
  void scan_callback(const sensor_msgs::msg::LaserScan::ConstSharedPtr scan_msg)
  {
    // Record arrival time so the watchdog knows the scan is fresh
    last_scan_time_ = now();

    const double ttc_threshold = get_parameter("ttc_threshold").as_double();
    const double release_distance = get_parameter("release_distance").as_double();
    const double release_cone_angle =
      get_parameter("release_cone_angle").as_double() * M_PI / 180.0;

    // Only forward motion is protected, so a negative (reversing) speed counts as zero
    const double forward_speed = std::max(speed_, 0.0);

    // Some drivers leave range_max unset (0); only enforce it when it is meaningful
    const bool check_range_max = scan_msg->range_max > scan_msg->range_min;

    // Smallest TTC over all beams (`inf` when stopped or nothing is being approached)
    double min_ttc = std::numeric_limits<double>::infinity();
    // Nearest obstacle in the front cone, used to decide when it is safe to release.
    // Starts at range_max: no valid front readings means nothing within sensor range.
    double min_front_distance = scan_msg->range_max;

    for (std::size_t i = 0; i < scan_msg->ranges.size(); ++i) {
      const double range = scan_msg->ranges[i];
      // Beam angle straight from the scan geometry (0 rad = straight ahead)
      const double angle =
        scan_msg->angle_min + static_cast<double>(i) * scan_msg->angle_increment;

      // Keep only readings the sensor itself reports as trustworthy:
      // finite (drops `inf`/`NaN`) and inside [range_min, range_max]
      if (!std::isfinite(range) || range <= 0.0 || range < scan_msg->range_min) {
        continue;
      }
      if (check_range_max && range > scan_msg->range_max) {
        continue;
      }

      // Closing speed of the beam: the component of the car's forward velocity along it.
      // TTC = range / closing speed, only for beams the car is actually approaching;
      // beams it is moving away from (or parallel to) can never collide.
      const double closing_speed = forward_speed * std::cos(angle);
      if (closing_speed > kMinClosingSpeed) {
        min_ttc = std::min(min_ttc, range / closing_speed);
      }

      // This node only ever commands forward motion, so the front is what must be clear
      if (std::abs(angle) < release_cone_angle) {
        min_front_distance = std::min(min_front_distance, range);
      }
    }

    // Debug logging
    RCLCPP_INFO(
      get_logger(), "🚦 TTC: %.2fs, Front: %.2fm (Brake <%gs, Release >%gm)",
      min_ttc, min_front_distance, ttc_threshold, release_distance);

    if (min_ttc < ttc_threshold) {
      // Latch the brake when the minimum valid TTC is below threshold
      if (!should_brake_) {
        RCLCPP_WARN(get_logger(), "🚨 Emergency Brake Activated!");
        should_brake_ = true;
        // Send the stop command now instead of waiting for the next timer tick
        publish_drive(0.0);
      }
    } else if (should_brake_ &&
      speed_ < kMinSpeedThreshold &&
      min_front_distance > release_distance)
    {
      // TTC is meaningless once stopped, so release on distance instead:
      // only when the car has come to rest and the front cone is clear
      RCLCPP_INFO(get_logger(), "🟢 Path is clear. Releasing brake.");
      should_brake_ = false;
    }
  }

  /**
   * @brief Find the sensor topics that have gone quiet.
   *
   * A topic is stale if no message has ever arrived on it, or if the last
   * one arrived more than `sensor_timeout` seconds ago.
   *
   * @return Names of the stale topics; empty when both /scan and /odom are fresh.
   */
  std::vector<std::string> stale_sensors()
  {
    const double timeout = get_parameter("sensor_timeout").as_double();
    const rclcpp::Time current_time = now();

    std::vector<std::string> stale;
    if (!last_scan_time_ || (current_time - *last_scan_time_).seconds() > timeout) {
      stale.push_back("/scan");
    }
    if (!last_odom_time_ || (current_time - *last_odom_time_).seconds() > timeout) {
      stale.push_back("/odom");
    }
    return stale;
  }

  /**
   * @brief Publish a timestamped drive command on /drive.
   *
   * @param speed Commanded speed in m/s; 0.0 stops the car.
   */
  void publish_drive(double speed)
  {
    ackermann_msgs::msg::AckermannDriveStamped drive_msg;
    drive_msg.header.stamp = now();
    drive_msg.drive.speed = static_cast<float>(speed);
    drive_publisher_->publish(drive_msg);
  }

  /**
   * @brief Publish the drive command for the current state; runs at 50Hz.
   *
   * The command is chosen in priority order:
   *
   *   1. Stop if /scan or /odom is stale (watchdog).
   *   2. Stop if scan_callback() has latched the brake.
   *   3. Otherwise drive forward at `cruise_speed`.
   */
  void drive_timer_callback()
  {
    const std::vector<std::string> stale = stale_sensors();
    if (!stale.empty()) {
      // Watchdog: never drive on missing or stale sensor data
      publish_drive(0.0);
      std::string topics;
      for (const std::string & topic : stale) {
        topics += (topics.empty() ? "" : ", ") + topic;
      }
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 1000,
        "🚨 Holding Brake: no recent data on %s", topics.c_str());
    } else if (should_brake_) {
      // Brake latched by scan_callback: keep commanding a stop
      publish_drive(0.0);
      RCLCPP_WARN(get_logger(), "🚨 Holding Brake: speed 0.0 m/s");
    } else {
      // Path is clear: drive at the configured cruise speed
      const double cruise_speed = get_parameter("cruise_speed").as_double();
      publish_drive(cruise_speed);
      RCLCPP_INFO(get_logger(), "🚗 Driving Forward: speed %.1f m/s", cruise_speed);
    }
  }

  // State shared between the callbacks
  double speed_{0.0};                            ///< Longitudinal speed from odometry (m/s)
  bool should_brake_{false};                     ///< Latched brake flag, set in scan_callback
  std::optional<rclcpp::Time> last_scan_time_;   ///< Arrival time of the last /scan (watchdog)
  std::optional<rclcpp::Time> last_odom_time_;   ///< Arrival time of the last /odom (watchdog)

  // ROS interfaces
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_subscriber_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_subscriber_;
  rclcpp::Publisher<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr drive_publisher_;
  rclcpp::TimerBase::SharedPtr drive_timer_;
};

/**
 * @brief Start the safety node and spin it until shutdown.
 *
 * @param argc Number of command-line arguments.
 * @param argv Command-line arguments passed to rclcpp.
 * @return 0 on clean shutdown.
 */
int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SafetyNode>());
  rclcpp::shutdown();
  return 0;
}
