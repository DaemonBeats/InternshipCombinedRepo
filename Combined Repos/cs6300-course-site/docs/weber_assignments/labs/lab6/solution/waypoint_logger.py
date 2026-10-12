#!/usr/bin/env python3
"""
Waypoint Logger — subscribes to /pf/pose/odom and saves poses to CSV.
Instructor solution for Lab 6.
"""

import csv
import os

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class WaypointLogger(Node):
    def __init__(self):
        super().__init__('waypoint_logger')

        self.csv_path = os.path.expanduser(
            '~/f1tenth_ws/src/pure_pursuit/maps/waypoints.csv'
        )
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

        self.csv_file = open(self.csv_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.count = 0

        self.subscription = self.create_subscription(
            Odometry,
            '/pf/pose/odom',
            self.odom_callback,
            10
        )

        self.get_logger().info(f'Waypoint logger started. Saving to {self.csv_path}')

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        z = msg.pose.pose.orientation.z
        w = msg.pose.pose.orientation.w

        self.csv_writer.writerow([x, y, z, w])
        self.count += 1

        if self.count % 50 == 0:
            self.get_logger().info(f'Recorded {self.count} waypoints')

    def destroy_node(self):
        self.csv_file.close()
        self.get_logger().info(
            f'Saved {self.count} waypoints to {self.csv_path}'
        )
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = WaypointLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
