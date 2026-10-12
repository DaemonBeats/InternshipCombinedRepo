#!/usr/bin/env python3
"""Automatic emergency braking node based on LiDAR time-to-collision (TTC)."""
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
import numpy as np

from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped
from rclpy.qos import qos_profile_sensor_data

class SafetyNode(Node):
    """
    The class that handles emergency braking based on LiDAR data.

    The node drives the car forward at a fixed cruise speed and stops it when
    the time-to-collision (TTC) with any obstacle ahead becomes too small.

    Data flow:
        /odom  -> odom_callback        -> stores the current speed
        /scan  -> scan_callback        -> computes TTC, latches/releases the brake
        timer  -> drive_timer_callback -> publishes the drive command at 50Hz

    Parameters:
        ttc_threshold (float): Brake when the TTC drops below this, in seconds.
        release_distance (float): Distance in metres the front cone must be
            clear before a latched brake is released.
        release_cone_angle (float): Half-width in degrees of the front cone
            checked for release.
        sensor_timeout (float): Brake if /scan or /odom is older than this,
            in seconds.
        cruise_speed (float): Speed in m/s commanded while the path is clear.
    """

    def __init__(self):
        """Set up the node state, parameters, subscribers, publisher and timer."""
        super().__init__('safety_node')

        # ✅ State shared between the callbacks
        self.speed = 0.0  # Longitudinal speed from odometry (m/s)
        self.should_brake = False  # Latched brake flag, set and cleared in scan_callback
        self.last_scan_time = None  # Arrival time of the last /scan (for the watchdog)
        self.last_odom_time = None  # Arrival time of the last /odom (for the watchdog)

        # ✅ Parameters
        self.declare_parameter('ttc_threshold', 0.5)  # Brake when TTC drops below this (s)
        self.declare_parameter('release_distance', 1.0)  # Front must be clear this far (m) to release
        self.declare_parameter('release_cone_angle', 20.0)  # Half-width of the front cone checked for release (deg)
        self.declare_parameter('sensor_timeout', 0.25)  # Brake if /scan or /odom is older than this (s)
        self.declare_parameter('cruise_speed', 1.0)  # Speed commanded while the path is clear (m/s)

        # ✅ Subscribers
        self.odom_subscriber_ = self.create_subscription(
            Odometry,
            "/odom",
            self.odom_callback,
            qos_profile_sensor_data)

        self.scan_subscriber_ = self.create_subscription(
            LaserScan,
            "/scan",
            self.scan_callback,
            qos_profile_sensor_data)

        # ✅ Publisher
        self.drive_publisher_ = self.create_publisher(
            AckermannDriveStamped,
            "/drive",
            10)

        # ✅ Timer (50Hz publishing)
        self.drive_timer = self.create_timer(0.02, self.drive_timer_callback)

    def odom_callback(self, odom_msg):
        """
        Store the car's current speed from an odometry message.

        Also records the arrival time so the watchdog in
        `drive_timer_callback` can tell that odometry is still fresh.

        Args:
            odom_msg (nav_msgs.msg.Odometry): Latest odometry; the speed is
                read from `twist.twist.linear.x` in m/s.
        """
        self.speed = odom_msg.twist.twist.linear.x
        self.last_odom_time = self.get_clock().now()
        self.get_logger().info(f"🛑 Current Speed: {self.speed:.2f} m/s")

    def scan_callback(self, scan_msg):
        """
        Compute the time-to-collision (TTC) from a LiDAR scan and update the brake.

        For every valid beam the closing speed is `speed * cos(angle)` and the
        TTC is `range / closing speed`. The smallest TTC over all beams decides
        the brake state:

        - Latch: the brake is set, and a stop command published immediately,
          when the smallest TTC falls below `ttc_threshold`.
        - Release: a latched brake is cleared only once the car has stopped
          and the nearest obstacle in the front cone is farther than
          `release_distance`. TTC cannot be used here because it is infinite
          when the car is not moving.

        Args:
            scan_msg (sensor_msgs.msg.LaserScan): Latest LiDAR scan. Angle 0 is
                straight ahead; ranges are in metres.
        """
        MIN_SPEED_THRESHOLD = 0.05  # Below this speed the car is considered stopped
        MIN_CLOSING_SPEED = 1e-3  # Below this closing speed a beam cannot collide (avoids divide by zero)

        # ✅ Record arrival time so the watchdog knows the scan is fresh
        self.last_scan_time = self.get_clock().now()

        ttc_threshold = self.get_parameter('ttc_threshold').value
        release_distance = self.get_parameter('release_distance').value
        release_cone_angle = np.deg2rad(self.get_parameter('release_cone_angle').value)

        # ✅ Beam angles straight from the scan geometry (0 rad = straight ahead)
        ranges = np.array(scan_msg.ranges)
        angles = scan_msg.angle_min + np.arange(ranges.size) * scan_msg.angle_increment

        # ✅ Keep only readings the sensor itself reports as trustworthy:
        #    finite (drops `inf`/`NaN`) and inside [range_min, range_max]
        valid_mask = np.isfinite(ranges) & (ranges > 0) & (ranges >= scan_msg.range_min)
        if scan_msg.range_max > scan_msg.range_min:
            valid_mask &= ranges <= scan_msg.range_max
        ranges = ranges[valid_mask]
        angles = angles[valid_mask]

        # ✅ Closing speed of every beam: the component of the car's forward velocity along it.
        #    Only forward motion is protected, so a negative (reversing) speed counts as zero.
        forward_speed = max(self.speed, 0.0)
        closing_speeds = forward_speed * np.cos(angles)

        # ✅ TTC = range / closing speed, only for beams the car is actually approaching.
        #    Beams the car is moving away from (or parallel to) can never collide.
        approaching = closing_speeds > MIN_CLOSING_SPEED
        ttc = ranges[approaching] / closing_speeds[approaching]

        # ✅ Smallest TTC over all beams (`inf` when stopped or nothing is being approached)
        min_ttc = np.min(ttc, initial=np.inf)

        # ✅ Nearest obstacle in the front cone, used to decide when it is safe to release.
        #    This node only ever commands forward motion, so the front is what must be clear.
        front_ranges = ranges[np.abs(angles) < release_cone_angle]
        # 🛑 No valid front readings means nothing within sensor range
        min_front_distance = np.min(front_ranges, initial=scan_msg.range_max)

        # 🔍 Debug Logging
        self.get_logger().info(
            f"🚦 TTC: {min_ttc:.2f}s, Front: {min_front_distance:.2f}m "
            f"(Brake <{ttc_threshold}s, Release >{release_distance}m)")

        # ✅ Latch the brake when the minimum valid TTC is below threshold
        if min_ttc < ttc_threshold:
            if not self.should_brake:
                self.get_logger().warn("🚨 Emergency Brake Activated!")
                self.should_brake = True
                # 🛑 Send the stop command now instead of waiting for the next timer tick
                self.publish_drive(0.0)
        # ✅ TTC is meaningless once stopped, so release on distance instead:
        #    only when the car has come to rest and the front cone is clear
        elif (self.should_brake
                and self.speed < MIN_SPEED_THRESHOLD
                and min_front_distance > release_distance):
            self.get_logger().info("🟢 Path is clear. Releasing brake.")
            self.should_brake = False

    def stale_sensors(self):
        """
        Find the sensor topics that have gone quiet.

        A topic is stale if no message has ever arrived on it, or if the last
        one arrived more than `sensor_timeout` seconds ago.

        Returns:
            list[str]: Names of the stale topics; empty when both /scan and
                /odom are fresh.
        """
        timeout = Duration(seconds=self.get_parameter('sensor_timeout').value)
        now = self.get_clock().now()
        last_times = (('/scan', self.last_scan_time), ('/odom', self.last_odom_time))
        return [topic for topic, stamp in last_times
                if stamp is None or now - stamp > timeout]

    def publish_drive(self, speed):
        """
        Publish a timestamped drive command on /drive.

        Args:
            speed (float): Commanded speed in m/s; 0.0 stops the car.
        """
        drive_msg = AckermannDriveStamped()
        drive_msg.header.stamp = self.get_clock().now().to_msg()
        drive_msg.drive.speed = speed
        self.drive_publisher_.publish(drive_msg)

    def drive_timer_callback(self):
        """
        Publish the drive command for the current state; runs at 50Hz.

        The command is chosen in priority order:

        1. Stop if /scan or /odom is stale (watchdog).
        2. Stop if `scan_callback` has latched the brake.
        3. Otherwise drive forward at `cruise_speed`.
        """
        # 🛑 Watchdog: never drive on missing or stale sensor data
        stale = self.stale_sensors()
        if stale:
            self.publish_drive(0.0)
            self.get_logger().warn(
                f"🚨 Holding Brake: no recent data on {', '.join(stale)}",
                throttle_duration_sec=1.0)
        # 🛑 Brake latched by scan_callback: keep commanding a stop
        elif self.should_brake:
            self.publish_drive(0.0)
            self.get_logger().warn("🚨 Holding Brake: speed 0.0 m/s")
        # ✅ Path is clear: drive at the configured cruise speed
        else:
            cruise_speed = self.get_parameter('cruise_speed').value
            self.publish_drive(cruise_speed)
            self.get_logger().info(f"🚗 Driving Forward: speed {cruise_speed:.1f} m/s")


def main(args=None):
    """
    Start the safety node and spin it until shutdown.

    Args:
        args (list[str], optional): Command-line arguments passed to rclpy.
            Defaults to None, which uses `sys.argv`.
    """
    rclpy.init(args=args)
    safety_node = SafetyNode()
    rclpy.spin(safety_node)
    safety_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
