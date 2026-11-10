#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node

import numpy as np
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped


class WallFollow(Node):
    """Implement Wall Following on the car."""

    def __init__(self):
        super().__init__('wall_follow_node')

        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('drive_topic', '/drive')

        lidarscan_topic = self.get_parameter('scan_topic').value
        drive_topic = self.get_parameter('drive_topic').value

        # subscribers and publishers
        self.scan_sub = self.create_subscription(LaserScan, lidarscan_topic, self.scan_callback, 10)
        self.drive_pub = self.create_publisher(AckermannDriveStamped, drive_topic, 10)

        # PID gains (tuned on levine_blocked; overridable as parameters)
        self.kp = self.declare_parameter('kp', 1.0).value
        self.kd = self.declare_parameter('kd', 0.1).value
        self.ki = self.declare_parameter('ki', 0.0).value

        # history
        self.integral = 0.0
        self.prev_error = 0.0
        self.error = 0.0
        self.d_filtered = 0.0
        self.prev_stamp = None
        self.restart_derivative = True

        # wall geometry
        self.desired_distance = self.declare_parameter('desired_distance', 0.8).value
        self.lookahead = self.declare_parameter('lookahead', 0.8).value
        self.theta = math.radians(50.0)  # angle between beam a and beam b

        # speed schedule (README: 0-10 deg, 10-20 deg, beyond)
        self.fast_speed = self.declare_parameter('fast_speed', 1.5).value
        self.mid_speed = self.declare_parameter('mid_speed', 1.0).value
        self.slow_speed = self.declare_parameter('slow_speed', 0.5).value
        self.max_steer = 0.4189  # f1tenth servo limit, rad

        # doorway handling: a sudden jump in the left wall distance with the
        # road ahead clear is an opening (doorway), not a corner, so hold
        # course instead of turning into it
        self.front_clear = 2.5  # m; anything farther than this ahead is "no wall ahead"
        self.jump = 0.4  # m; beam increase that counts as the wall opening up
        self.max_hold = 2.0  # s; never hold course longer than this
        self.ref_tau = 0.1  # s; time constant of the beam reference filters
        self.d_tau = 0.05  # s; time constant of the derivative filter
        self.a_ref = None
        self.b_ref = None
        self.holding = False
        self.held = 0.0

        # filled in from each scan for get_range()
        self.angle_min = 0.0
        self.angle_increment = 1.0

    def get_range(self, range_data, angle):
        """
        Simple helper to return the corresponding range measurement at a given angle.

        Args:
            range_data: single range array from the LiDAR
            angle: between angle_min and angle_max of the LiDAR

        Returns:
            range: range measurement in meters at the given angle
        """
        i = int(round((angle - self.angle_min) / self.angle_increment))
        i = min(max(i, 0), len(range_data) - 1)
        # average a few neighbouring beams to smooth out single-beam noise
        window = np.asarray(range_data[max(i - 2, 0):i + 3])
        window = window[np.isfinite(window)]
        if len(window) == 0:
            return 30.0  # nothing returned: treat as open space
        return float(np.mean(window))

    def get_error(self, range_data, dist, dt):
        """
        Calculate wall-following error for the left wall.

        Args:
            range_data: single range array from the LiDAR
            dist: desired distance to the wall
            dt: time since the previous scan, in seconds

        Returns:
            error: calculated error (0 while holding course through an opening)
        """
        b = self.get_range(range_data, math.pi / 2)
        a = self.get_range(range_data, math.pi / 2 - self.theta)
        front = min(self.get_range(range_data, math.radians(k)) for k in (-5.0, 0.0, 5.0))

        if self.a_ref is None:
            self.a_ref, self.b_ref = a, b

        # a corner has a wall ahead, a doorway does not
        if self.holding:
            self.held += dt
            wall_back = a * math.cos(self.theta) - b < self.jump / 2 and b - self.b_ref < self.jump / 2
            if front < self.front_clear or wall_back or self.held > self.max_hold:
                self.holding = False
            else:
                return 0.0
        elif front > self.front_clear and (a - self.a_ref > self.jump or b - self.b_ref > self.jump):
            self.holding = True
            self.held = 0.0
            return 0.0

        k = dt / (self.ref_tau + dt)
        self.a_ref += k * (a - self.a_ref)
        self.b_ref += k * (b - self.b_ref)

        alpha = math.atan2(a * math.cos(self.theta) - b, a * math.sin(self.theta))
        d_t = b * math.cos(alpha)
        d_next = d_t + self.lookahead * math.sin(alpha)
        # positive error: too close to the left wall
        return dist - d_next

    def pid_control(self, error, dt):
        """
        Based on the calculated error, publish vehicle control.

        Args:
            error: calculated error
            dt: time since the previous scan, in seconds
        """
        self.integral = float(np.clip(self.integral + error * dt, -1.0, 1.0))
        derivative = (error - self.prev_error) / dt
        self.prev_error = error
        self.d_filtered += dt / (self.d_tau + dt) * (derivative - self.d_filtered)

        # steering left is positive, so too close to the left wall steers right
        u = self.kp * error + self.ki * self.integral + self.kd * self.d_filtered
        angle = float(np.clip(-u, -self.max_steer, self.max_steer))
        self.publish_drive(angle, self.speed_for(angle))

    def speed_for(self, angle):
        """Step the speed down as the steering angle grows."""
        deg = abs(math.degrees(angle))
        if deg < 10.0:
            return self.fast_speed
        if deg < 20.0:
            return self.mid_speed
        return self.slow_speed

    def publish_drive(self, angle, speed):
        drive_msg = AckermannDriveStamped()
        drive_msg.header.stamp = self.get_clock().now().to_msg()
        drive_msg.drive.steering_angle = angle
        drive_msg.drive.speed = speed
        self.drive_pub.publish(drive_msg)

    def scan_callback(self, msg):
        """
        Callback function for LaserScan messages.

        Args:
            msg: Incoming LaserScan message
        """
        self.angle_min = msg.angle_min
        self.angle_increment = msg.angle_increment

        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        dt = 0.01 if self.prev_stamp is None else stamp - self.prev_stamp
        if not 0.0 < dt < 0.5:
            dt = 0.01
        self.prev_stamp = stamp

        error = self.get_error(msg.ranges, self.desired_distance, dt)
        if self.holding:
            # drive straight through the opening
            self.publish_drive(0.0, self.mid_speed)
            self.restart_derivative = True
            return

        if self.restart_derivative:
            # first scan, or just left an opening: no derivative kick
            self.prev_error = error
            self.restart_derivative = False
        self.error = error
        self.pid_control(error, dt)


def main(args=None):
    rclpy.init(args=args)
    print("WallFollow Initialized")
    wall_follow_node = WallFollow()
    rclpy.spin(wall_follow_node)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    wall_follow_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()