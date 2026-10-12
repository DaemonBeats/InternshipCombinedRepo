.. _doc_tutorials_building_pure_pursuit_node:

Building the Pure Pursuit Node
===============================

With waypoints recorded, the next step is to build the node that reads them and drives the car autonomously. This tutorial walks through the Pure Pursuit algorithm and the ROS 2 infrastructure around it.

.. note::

   This tutorial covers the concepts behind the code. For the graded assignment with deliverables, see **Lab 6b - Pure Pursuit** in the Weber Assignments.

How Pure Pursuit Works
-----------------------

Pure Pursuit is a geometric path tracking algorithm. The idea is simple: pick a point on the path some distance ahead of the car (the **lookahead point**), then steer along a circular arc to reach it.

On each update cycle:

1. Read the car's current pose from the particle filter
2. Find the **closest waypoint** to the car
3. Search forward along the path to find the first waypoint at least ``lookahead_distance`` away --- this is the **lookahead point**
4. Transform the lookahead point into the car's local frame
5. Compute the steering angle using the Pure Pursuit formula
6. Publish a drive command

The **lookahead distance** is the key tuning parameter. A shorter lookahead tracks the path more tightly but can cause oscillation. A longer lookahead produces smoother driving but cuts corners.

Step 1 --- Create the Config File
-----------------------------------

ROS 2 parameters let you change behavior without editing code. Create ``~/f1tenth_ws/src/pure_pursuit/config/pure_pursuit.yaml``:

.. code-block:: yaml

   pure_pursuit_node:
     ros__parameters:
       lookahead_distance: 1.5
       speed: 1.0
       waypoint_file: "waypoints.csv"

.. important::

   The top-level key ``pure_pursuit_node:`` must match the node name in **three** places:

   1. ``super().__init__('pure_pursuit_node')`` in your Python class
   2. ``name='pure_pursuit_node'`` in the launch file
   3. The YAML key shown above

   If any of these don't match, ROS 2 silently ignores the parameters and uses defaults.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Parameter
     - Purpose
   * - ``lookahead_distance``
     - How far ahead on the path to steer toward (meters). Start at 1.5 and tune from there.
   * - ``speed``
     - Forward drive speed in m/s. Start low (0.5) for safety.
   * - ``waypoint_file``
     - Name of the CSV file in the ``maps/`` directory.

Step 2 --- Create the Launch File
-----------------------------------

A launch file lets you start the node with its config in one command. Create ``~/f1tenth_ws/src/pure_pursuit/launch/pure_pursuit_launch.py``:

.. code-block:: python

   from launch import LaunchDescription
   from launch_ros.actions import Node
   from ament_index_python.packages import get_package_share_directory
   import os


   def generate_launch_description():
       config = os.path.join(
           get_package_share_directory('pure_pursuit'),
           'config',
           'pure_pursuit.yaml'
       )

       return LaunchDescription([
           Node(
               package='pure_pursuit',
               executable='pure_pursuit_node',
               name='pure_pursuit_node',
               parameters=[config],
               output='screen'
           )
       ])

Key points:

- ``get_package_share_directory()`` finds the installed config path (inside ``install/``, not ``src/``)
- ``parameters=[config]`` loads the YAML file as node parameters
- ``output='screen'`` sends log output to the terminal

Step 3 --- Update setup.py
----------------------------

Tell the build system to install the config, launch, and map files. Add these to the ``data_files`` list in ``setup.py``:

.. code-block:: python

   (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
   (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
   (os.path.join('share', package_name, 'maps'), glob('maps/*.csv')),

Also add the Pure Pursuit node entry point alongside the existing waypoint logger:

.. code-block:: python

   entry_points={
       'console_scripts': [
           'waypoint_logger = pure_pursuit.waypoint_logger:main',
           'pure_pursuit_node = pure_pursuit.pure_pursuit_node:main',
       ],
   },

Step 4 --- Write the Node
---------------------------

Create ``~/f1tenth_ws/src/pure_pursuit/pure_pursuit/pure_pursuit_node.py``. The node has several components:

Loading Parameters
^^^^^^^^^^^^^^^^^^^

Declare and read parameters from the config file:

.. code-block:: python

   self.declare_parameter('lookahead_distance', 1.5)
   self.declare_parameter('speed', 1.0)
   self.declare_parameter('waypoint_file', 'waypoints.csv')

   self.lookahead = self.get_parameter('lookahead_distance').value
   self.speed = self.get_parameter('speed').value

Loading Waypoints from CSV
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Read the waypoint file at startup and store the poses as a list:

.. code-block:: python

   import csv

   waypoints = []
   with open(filepath, 'r') as f:
       reader = csv.reader(f)
       for row in reader:
           waypoints.append((float(row[0]), float(row[1]),
                             float(row[2]), float(row[3])))

Each row contains ``(x, y, orientation_z, orientation_w)`` --- the same four values your waypoint logger recorded.

Subscriber and Publisher
^^^^^^^^^^^^^^^^^^^^^^^^^

The node subscribes to the particle filter for the car's position and publishes drive commands:

.. code-block:: python

   from nav_msgs.msg import Odometry
   from ackermann_msgs.msg import AckermannDriveStamped

   # Subscriber: car's current pose
   self.create_subscription(Odometry, '/pf/pose/odom', self.pose_callback, 10)

   # Publisher: drive commands
   self.drive_pub = self.create_publisher(AckermannDriveStamped, '/drive', 10)

The Pure Pursuit Algorithm
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inside the callback, implement the algorithm in four stages:

**1. Find the closest waypoint**

Compute the Euclidean distance from the car to every waypoint and find the nearest one:

.. code-block:: python

   import math

   # Car's current position
   cx = msg.pose.pose.position.x
   cy = msg.pose.pose.position.y

   # Find closest waypoint index
   min_dist = float('inf')
   closest_idx = 0
   for i, (wx, wy, _, _) in enumerate(self.waypoints):
       dist = math.sqrt((wx - cx)**2 + (wy - cy)**2)
       if dist < min_dist:
           min_dist = dist
           closest_idx = i

**2. Find the lookahead point**

Starting from the closest waypoint, search forward along the path until you find a waypoint at least ``lookahead_distance`` away:

.. code-block:: python

   lookahead_point = None
   n = len(self.waypoints)
   for i in range(n):
       idx = (closest_idx + i) % n       # wrap around the path
       wx, wy = self.waypoints[idx][0], self.waypoints[idx][1]
       dist = math.sqrt((wx - cx)**2 + (wy - cy)**2)
       if dist >= self.lookahead:
           lookahead_point = (wx, wy)
           break

The modulo ``% n`` wraps the search back to the beginning of the waypoint list, allowing the car to drive continuous laps.

**3. Transform to the car's local frame**

The car needs to know if the lookahead point is to its **left** or **right**. Transform from the map frame to the car's frame:

.. code-block:: python

   # Get car's heading from quaternion
   qz = msg.pose.pose.orientation.z
   qw = msg.pose.pose.orientation.w
   heading = 2.0 * math.atan2(qz, qw)

   # Translate
   dx = lookahead_point[0] - cx
   dy = lookahead_point[1] - cy

   # Rotate into car's local frame
   local_x = dx * math.cos(-heading) - dy * math.sin(-heading)
   local_y = dx * math.sin(-heading) + dy * math.cos(-heading)

After this transform:

- ``local_x`` is how far ahead the point is
- ``local_y`` is the lateral offset (positive = left, negative = right)

**4. Compute steering angle and publish**

The Pure Pursuit formula computes the curvature of the arc that connects the car to the lookahead point:

.. code-block:: text

   steering_angle = 2 * y / L^2

Where ``L`` is the distance to the lookahead point and ``y`` is the lateral offset in the car's frame:

.. code-block:: python

   L = math.sqrt(local_x**2 + local_y**2)
   steering_angle = 2.0 * local_y / (L ** 2)

   # Publish the drive command
   drive_msg = AckermannDriveStamped()
   drive_msg.drive.steering_angle = steering_angle
   drive_msg.drive.speed = self.speed
   self.drive_pub.publish(drive_msg)

This formula comes from the geometry of a circular arc. When ``local_y`` is zero (the lookahead point is straight ahead), the steering angle is zero. When the point is to the left, the car steers left, and vice versa.

Step 5 --- Build and Test
---------------------------

.. code-block:: bash

   cd ~/f1tenth_ws
   colcon build --packages-select pure_pursuit
   source install/setup.bash

Verify the launch file works:

.. code-block:: bash

   ros2 launch pure_pursuit pure_pursuit_launch.py

If the node starts without errors (it will wait for ``/pf/pose/odom`` messages), the build is correct. See :ref:`doc_tutorials_pure_pursuit_node` for full instructions on running it with the particle filter on the robot.

Understanding the Math
-----------------------

The Pure Pursuit steering formula ``2y / L^2`` is derived from the geometry of a circular arc connecting the car's rear axle to the lookahead point.

Given a circle of radius ``R`` passing through the origin (car) and the lookahead point at distance ``L`` with lateral offset ``y``:

.. code-block:: text

   curvature = 1/R = 2y / L^2

The steering angle is then proportional to this curvature. The Ackermann steering model converts curvature to a wheel angle, but for a simple implementation the curvature value works directly as the steering command.

**Intuition:**

- Far lookahead (large ``L``) + small ``y`` = gentle steering = smooth driving
- Close lookahead (small ``L``) + large ``y`` = aggressive steering = tight tracking

This is why ``lookahead_distance`` is the primary tuning knob.

Key Concepts Recap
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Concept
     - What You Learned
   * - ROS 2 Parameters
     - Declaring, loading from YAML, and using runtime parameters
   * - Launch Files
     - Starting nodes with config files using ``launch_ros``
   * - ``setup.py`` data files
     - Installing config, launch, and data files with the package
   * - Pure Pursuit Algorithm
     - Closest waypoint search, lookahead point, coordinate transforms, steering formula
   * - Coordinate Transforms
     - Converting map-frame points to the car's local frame using rotation
   * - ``AckermannDriveStamped``
     - Publishing steering angle and speed commands to ``/drive``
