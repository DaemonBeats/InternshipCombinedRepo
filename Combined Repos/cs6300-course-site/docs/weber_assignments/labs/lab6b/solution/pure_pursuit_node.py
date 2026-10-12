#!/usr/bin/env python3
"""
Pure Pursuit Node — follows recorded waypoints using geometric path tracking.
Instructor solution for Lab 6b.
"""

import csv
import math
import os

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped
from ament_index_python.packages import get_package_share_directory


class PurePursuitNode(Node):
    def __init__(self):
        super().__init__('pure_pursuit_node')

        self.declare_parameter('lookahead_distance', 1.5)
        self.declare_parameter('speed', 1.0)
        self.declare_parameter('waypoint_file', 'waypoints.csv')

        self.lookahead = self.get_parameter('lookahead_distance').value
        self.speed = self.get_parameter('speed').value
        waypoint_file = self.get_parameter('waypoint_file').value

        # Load waypoints from CSV
        maps_dir = os.path.join(
            get_package_share_directory('pure_pursuit'), 'maps'
        )
        csv_path = os.path.join(maps_dir, waypoint_file)
        self.waypoints = []
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                x, y, z, w = float(row[0]), float(row[1]), float(row[2]), float(row[3])
                self.waypoints.append((x, y, z, w))

        self.get_logger().info(
            f'Loaded {len(self.waypoints)} waypoints from {csv_path}'
        )
        self.get_logger().info(
            f'Lookahead: {self.lookahead} m, Speed: {self.speed} m/s'
        )

        self.drive_pub = self.create_publisher(
            AckermannDriveStamped, '/drive', 10
        )

        self.subscription = self.create_subscription(
            Odometry, '/pf/pose/odom', self.odom_callback, 10
        )

    def odom_callback(self, msg):
        # Current pose
        cx = msg.pose.pose.position.x
        cy = msg.pose.pose.position.y
        cz = msg.pose.pose.orientation.z
        cw = msg.pose.pose.orientation.w
        heading = 2.0 * math.atan2(cz, cw)

        # Find closest waypoint
        min_dist = float('inf')
        closest_idx = 0
        for i, (wx, wy, _, _) in enumerate(self.waypoints):
            dist = math.hypot(wx - cx, wy - cy)
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        # Find lookahead point — search forward from closest, wrapping around
        lookahead_point = None
        n = len(self.waypoints)
        for i in range(n):
            idx = (closest_idx + i) % n
            wx, wy = self.waypoints[idx][0], self.waypoints[idx][1]
            dist = math.hypot(wx - cx, wy - cy)
            if dist >= self.lookahead:
                lookahead_point = (wx, wy)
                break

        if lookahead_point is None:
            # All waypoints are closer than lookahead — use the farthest one
            lookahead_point = (
                self.waypoints[(closest_idx + n // 2) % n][0],
                self.waypoints[(closest_idx + n // 2) % n][1],
            )

        # Transform lookahead point to car's local frame
        dx = lookahead_point[0] - cx
        dy = lookahead_point[1] - cy
        local_x = dx * math.cos(-heading) - dy * math.sin(-heading)
        local_y = dx * math.sin(-heading) + dy * math.cos(-heading)

        # Pure Pursuit steering formula
        L = math.hypot(local_x, local_y)
        if L < 0.001:
            steering_angle = 0.0
        else:
            steering_angle = 2.0 * local_y / (L * L)

        # Publish drive command
        drive_msg = AckermannDriveStamped()
        drive_msg.drive.steering_angle = steering_angle
        drive_msg.drive.speed = self.speed
        self.drive_pub.publish(drive_msg)


def main(args=None):
    rclpy.init(args=args)
    node = PurePursuitNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
