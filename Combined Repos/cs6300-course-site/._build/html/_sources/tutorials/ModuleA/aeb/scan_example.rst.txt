.. _doc_tutorials_aeb_scan_example:

AEB Scan Example
================

🚀 How safety_node.py Identifies Front Readings from LiDAR
-----------------------------------------------------------

The safety node uses LiDAR data to detect obstacles and stop the car if necessary. However, if an obstacle is on the side (e.g., a wall), we don't want the car to stop unnecessarily.

🔹 Problem Before Fix
~~~~~~~~~~~~~~~~~~~~~

- The car stopped for any obstacle, even if it was on the side
- Example: A wall on the right triggered braking, even though the front was clear

✅ Fix: Filter Only Front Readings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure only front-facing obstacles are considered, we modify the ``scan_callback()`` function.

1️⃣ Understanding LiDAR Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The LiDAR sensor provides:

- ``ranges[]`` → A list of distances measured at different angles
- ``angle_min`` → The starting angle of the scan (e.g., -135°)
- ``angle_max`` → The ending angle of the scan (e.g., +135°)
- ``angle_increment`` → The angle gap between two measurements

**Example Angle Mapping:**

.. code-block:: text

   (-135°)    (-90°)    (0° Front)    (+90°)    (+135°)
      |----------|----------|----------|----------|
   Left Side  Left Front  Forward  Right Front  Right Side

- The center of the car is at **0°**
- The leftmost reading is at ``angle_min`` (e.g., -135°)
- The rightmost reading is at ``angle_max`` (e.g., +135°)
- Angles near **0°** correspond to objects directly in front of the car

2️⃣ Extracting Front Readings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following Python code ensures we only analyze front obstacles (±20° from center):

.. code-block:: python

   # ✅ Compute angles for each LiDAR measurement
   angles = np.linspace(scan_msg.angle_min, scan_msg.angle_max, len(scan_msg.ranges))

   # ✅ Define the front-facing region (e.g., ±20° from center)
   front_angle_range = np.deg2rad(20)  # Convert 20° to radians

   # ✅ Identify indices where angles are within the front range
   front_indices = np.where(np.abs(angles) < front_angle_range)

   # ✅ Extract front readings based on selected indices
   front_ranges = np.array(scan_msg.ranges)[front_indices]
   front_angles = angles[front_indices]
   front_cos_angles = np.cos(front_angles)

📌 Explanation of Code
~~~~~~~~~~~~~~~~~~~~~~

**1️⃣ Compute Angles for Each Measurement**

.. code-block:: python

   np.linspace(angle_min, angle_max, len(ranges))

This generates an array of angles corresponding to each LiDAR distance.

**Example:**

.. code-block:: text

   angles = [-135°, -120°, -105°, ..., 0°, ..., +105°, +120°, +135°]

**2️⃣ Select Only the Front Angles (±20°)**

.. code-block:: python

   np.deg2rad(20) → Converts 20 degrees to radians (0.349 rad)
   np.abs(angles) < front_angle_range → Finds all angles between -20° and +20°

**Example:**

.. code-block:: text

   Front Angles: [-15°, -10°, -5°, 0°, +5°, +10°, +15°]

**3️⃣ Extract Corresponding LiDAR Readings**

.. code-block:: python

   front_ranges = ranges[front_indices]  # Keeps only distances in the front zone
   front_angles = angles[front_indices]  # Keeps only angles in the front zone

Now we ignore obstacles on the sides! 🎯

3️⃣ Why This Fix Works
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - 🚗 Before Fix
     - ✅ After Fix
   * - Car stops for any obstacle
     - Car stops only for obstacles in front
   * - Wall on the right triggers braking
     - Car ignores side walls
   * - Driving next to a wall = false stops
     - Car moves smoothly near side obstacles

4️⃣ Summary
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Step
     - What It Does
   * - 1️⃣ Compute angles
     - Maps each LiDAR reading to its corresponding angle
   * - 2️⃣ Filter front angles
     - Keeps only readings within -20° to +20°
   * - 3️⃣ Extract front distances
     - Only analyzes obstacles directly in front
   * - 4️⃣ Compute TTC
     - Uses these front readings for safety decisions
   * - 5️⃣ Stop only if necessary
     - The car won't brake for side walls anymore

5️⃣ Full Code Example
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   import rclpy
   from rclpy.node import Node
   import numpy as np

   # ✅ ROS 2 message headers
   from sensor_msgs.msg import LaserScan
   from nav_msgs.msg import Odometry


   class SafetyNode(Node):
       """
       A minimal ROS 2 node to **debug raw LiDAR scan data** and verify TTC calculations.
       """

       def __init__(self):
           super().__init__('safety_node')

           self.speed = 0.0  # Initialize vehicle speed

           # ✅ Subscribers: Listening for speed & LiDAR data
           self.create_subscription(LaserScan, "/scan", self.scan_callback, 10)

           self.get_logger().info("✅ Raw LiDAR Debugging Node Started!")


       def scan_callback(self, scan_msg):
           """Processes LiDAR data and logs raw front-facing scan readings."""

           # ✅ Compute angles for each LiDAR measurement
           angles = np.linspace(scan_msg.angle_min, scan_msg.angle_max, len(scan_msg.ranges))

           # ✅ Define the front-facing region (e.g., ±20° from center)
           front_angle_range = np.deg2rad(20)  # Convert 20° to radians
           front_indices = np.where(np.abs(angles) < front_angle_range)

           # ✅ Extract front readings
           front_ranges = np.array(scan_msg.ranges)[front_indices]
           front_angles = angles[front_indices]

           # ✅ Print raw LiDAR scan data (first 10 values for readability)
           # self.get_logger().info(f"📡 Raw Front Scan Angles (deg): {np.rad2deg(front_angles[:10])}")
           self.get_logger().info(f"📏 Raw Front Scan Ranges (m): {front_ranges[:10]}")

           # ✅ Check for invalid values
           if len(front_ranges) == 0 or np.all(np.isinf(front_ranges)):
               self.get_logger().warn("⚠️ No valid front LiDAR readings! (All inf values)")

           # ✅ Find the **closest** detected object in the front region
           min_range = np.min(front_ranges) if len(front_ranges) > 0 else np.inf
           self.get_logger().info(f"🎯 Closest Object in Front: {min_range:.2f} meters")



   def main(args=None):
       rclpy.init(args=args)
       safety_node = SafetyNode()
       rclpy.spin(safety_node)
       safety_node.destroy_node()
       rclpy.shutdown()


   if __name__ == '__main__':
       main()
