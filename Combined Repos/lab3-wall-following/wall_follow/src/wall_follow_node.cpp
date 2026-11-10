#include "rclcpp/rclcpp.hpp"
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>
#include "sensor_msgs/msg/laser_scan.hpp"
#include "ackermann_msgs/msg/ackermann_drive_stamped.hpp"

class WallFollow : public rclcpp::Node {

public:
    WallFollow() : Node("wall_follow_node")
    {
        declare_parameter("scan_topic", "/scan");
        declare_parameter("drive_topic", "/drive");
        lidarscan_topic = get_parameter("scan_topic").as_string();
        drive_topic = get_parameter("drive_topic").as_string();

        // PID gains and geometry, tuned on levine_blocked; overridable as parameters
        kp = this->declare_parameter("kp", kp);
        kd = this->declare_parameter("kd", kd);
        ki = this->declare_parameter("ki", ki);
        desired_distance = this->declare_parameter("desired_distance", desired_distance);
        lookahead = this->declare_parameter("lookahead", lookahead);
        fast_speed = this->declare_parameter("fast_speed", fast_speed);
        mid_speed = this->declare_parameter("mid_speed", mid_speed);
        slow_speed = this->declare_parameter("slow_speed", slow_speed);

        scan_sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
            lidarscan_topic, 10,
            std::bind(&WallFollow::scan_callback, this, std::placeholders::_1));
        drive_pub_ = this->create_publisher<ackermann_msgs::msg::AckermannDriveStamped>(drive_topic, 10);
    }

private:
    // PID CONTROL PARAMS
    double kp = 1.0;
    double kd = 0.1;
    double ki = 0.0;
    double servo_offset = 0.0;
    double prev_error = 0.0;
    double error = 0.0;
    double integral = 0.0;
    double d_filtered = 0.0;
    bool restart_derivative = true;

    // Wall geometry
    double desired_distance = 0.8;
    double lookahead = 0.8;
    const double theta = 50.0 * M_PI / 180.0;  // angle between beam a and beam b

    // Speed schedule (README: 0-10 deg, 10-20 deg, beyond)
    double fast_speed = 1.5;
    double mid_speed = 1.0;
    double slow_speed = 0.5;
    const double max_steer = 0.4189;  // f1tenth servo limit, rad

    // Doorway handling: a sudden jump in the left wall distance with the road
    // ahead clear is an opening (doorway), not a corner, so hold course instead
    // of turning into it
    const double front_clear = 2.5;  // m; anything farther than this ahead is "no wall ahead"
    const double jump = 0.4;         // m; beam increase that counts as the wall opening up
    const double max_hold = 2.0;     // s; never hold course longer than this
    const double ref_tau = 0.1;      // s; time constant of the beam reference filters
    const double d_tau = 0.05;       // s; time constant of the derivative filter
    bool have_ref = false;
    double a_ref = 0.0;
    double b_ref = 0.0;
    bool holding = false;
    double held = 0.0;

    // Filled in from each scan for get_range()
    double angle_min = 0.0;
    double angle_increment = 1.0;
    double prev_stamp = -1.0;

    // Topics
    std::string lidarscan_topic = "/scan";
    std::string drive_topic = "/drive";
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
    rclcpp::Publisher<ackermann_msgs::msg::AckermannDriveStamped>::SharedPtr drive_pub_;

    double get_range(const std::vector<float>& range_data, double angle)
    {
        /*
        Simple helper to return the corresponding range measurement at a given angle. Make sure you take care of NaNs and infs.

        Args:
            range_data: single range array from the LiDAR
            angle: between angle_min and angle_max of the LiDAR

        Returns:
            range: range measurement in meters at the given angle
        */

        const int n = static_cast<int>(range_data.size());
        int i = static_cast<int>(std::lround((angle - angle_min) / angle_increment));
        i = std::min(std::max(i, 0), n - 1);
        // average a few neighbouring beams to smooth out single-beam noise
        double sum = 0.0;
        int count = 0;
        for (int j = std::max(i - 2, 0); j <= std::min(i + 2, n - 1); ++j) {
            if (std::isfinite(range_data[j])) {
                sum += range_data[j];
                ++count;
            }
        }
        if (count == 0) {
            return 30.0;  // nothing returned: treat as open space
        }
        return sum / count;
    }

    double get_error(const std::vector<float>& range_data, double dist, double dt)
    {
        /*
        Calculates the error to the wall. Follow the wall to the left (going counter clockwise in the Levine loop). You potentially will need to use get_range()

        Args:
            range_data: single range array from the LiDAR
            dist: desired distance to the wall

        Returns:
            error: calculated error
        */

        const double b = get_range(range_data, M_PI / 2);
        const double a = get_range(range_data, M_PI / 2 - theta);
        const double cone = 5.0 * M_PI / 180.0;
        const double front = std::min({get_range(range_data, -cone),
                                       get_range(range_data, 0.0),
                                       get_range(range_data, cone)});

        if (!have_ref) {
            a_ref = a;
            b_ref = b;
            have_ref = true;
        }

        // a corner has a wall ahead, a doorway does not
        if (holding) {
            held += dt;
            const bool wall_back = a * std::cos(theta) - b < jump / 2 && b - b_ref < jump / 2;
            if (front < front_clear || wall_back || held > max_hold) {
                holding = false;
            } else {
                return 0.0;
            }
        } else if (front > front_clear && (a - a_ref > jump || b - b_ref > jump)) {
            holding = true;
            held = 0.0;
            return 0.0;
        }

        const double k = dt / (ref_tau + dt);
        a_ref += k * (a - a_ref);
        b_ref += k * (b - b_ref);

        const double alpha = std::atan2(a * std::cos(theta) - b, a * std::sin(theta));
        const double d_t = b * std::cos(alpha);
        const double d_next = d_t + lookahead * std::sin(alpha);
        // positive error: too close to the left wall
        return dist - d_next;
    }

    void pid_control(double error, double dt)
    {
        /*
        Based on the calculated error, publish vehicle control

        Args:
            error: calculated error
            dt: time since the previous scan, in seconds

        Returns:
            None
        */
        integral = std::clamp(integral + error * dt, -1.0, 1.0);
        const double derivative = (error - prev_error) / dt;
        prev_error = error;
        d_filtered += dt / (d_tau + dt) * (derivative - d_filtered);

        // steering left is positive, so too close to the left wall steers right
        const double u = kp * error + ki * integral + kd * d_filtered;
        const double angle = std::clamp(-u + servo_offset, -max_steer, max_steer);
        publish_drive(angle, speed_for(angle));
    }

    double speed_for(double angle)
    {
        // step the speed down as the steering angle grows
        const double deg = std::abs(angle) * 180.0 / M_PI;
        if (deg < 10.0) {
            return fast_speed;
        }
        if (deg < 20.0) {
            return mid_speed;
        }
        return slow_speed;
    }

    void publish_drive(double angle, double speed)
    {
        auto drive_msg = ackermann_msgs::msg::AckermannDriveStamped();
        drive_msg.header.stamp = this->now();
        drive_msg.drive.steering_angle = angle;
        drive_msg.drive.speed = speed;
        drive_pub_->publish(drive_msg);
    }

    void scan_callback(const sensor_msgs::msg::LaserScan::ConstSharedPtr scan_msg)
    {
        /*
        Callback function for LaserScan messages. Calculate the error and publish the drive message in this function.

        Args:
            msg: Incoming LaserScan message

        Returns:
            None
        */
        angle_min = scan_msg->angle_min;
        angle_increment = scan_msg->angle_increment;

        const double stamp = rclcpp::Time(scan_msg->header.stamp).seconds();
        double dt = prev_stamp < 0.0 ? 0.01 : stamp - prev_stamp;
        if (!(dt > 0.0 && dt < 0.5)) {
            dt = 0.01;
        }
        prev_stamp = stamp;

        const double err = get_error(scan_msg->ranges, desired_distance, dt);
        if (holding) {
            // drive straight through the opening
            publish_drive(0.0, mid_speed);
            restart_derivative = true;
            return;
        }

        if (restart_derivative) {
            // first scan, or just left an opening: no derivative kick
            prev_error = err;
            restart_derivative = false;
        }
        error = err;
        pid_control(err, dt);

    }

};
int main(int argc, char ** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<WallFollow>());
    rclcpp::shutdown();
    return 0;
}