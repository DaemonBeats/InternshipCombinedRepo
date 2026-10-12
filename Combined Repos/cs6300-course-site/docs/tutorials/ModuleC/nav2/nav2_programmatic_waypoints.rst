.. _doc_tutorials_nav2_programmatic_waypoints:

Programmatic Waypoint Navigation
=================================

Send the car through multiple waypoints using a Python ROS 2 action client instead of clicking in the RViz2 GUI.

In the previous tutorials you sent goals by clicking in RViz2. That works for testing, but for autonomous racing you need repeatable routes that run without manual interaction. In this tutorial you will write a Python node that sends a list of waypoints to Nav2 programmatically.

What is an Action Client?
--------------------------

ROS 2 has three communication patterns:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Pattern
     - Behavior
     - Example
   * - **Topic**
     - One-way publish/subscribe (fire-and-forget)
     - ``/scan``, ``/cmd_vel``
   * - **Service**
     - Synchronous request → response (blocks until done)
     - Setting a parameter
   * - **Action**
     - Asynchronous goal → feedback → result (cancelable)
     - Nav2 navigation

Nav2 exposes its navigation capabilities as **action servers**. When you click 2D Goal Pose in RViz2, RViz2 is acting as an action client — it sends a goal to Nav2's ``/navigate_to_pose`` action server. The ``/navigate_through_poses`` action server accepts a *list* of poses and drives through all of them in order.

In this tutorial you will write your own action client that does the same thing — but from code instead of the GUI.

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Field
     - Type
     - Description
   * - Goal
     - ``geometry_msgs/PoseStamped[]``
     - List of poses to navigate through
   * - Feedback
     - ``current_pose``, ``number_of_poses_remaining``
     - Progress updates during navigation
   * - Result
     - (empty)
     - Returned on success or failure

How to Get Waypoint Coordinates
--------------------------------

Before writing the node, you need map coordinates for your waypoints. The easiest way is to use ``ros2 topic echo`` while clicking in RViz2:

1. With Nav2 running and the map visible in RViz2, open a terminal:

   .. code-block:: bash

      ros2 topic echo /goal_pose

2. In RViz2, click **2D Goal Pose** and place it at a desired waypoint location.

3. The terminal prints a ``PoseStamped`` message. Copy the values you need:

   .. code-block:: text

      header:
        frame_id: map
      pose:
        position:
          x: 1.234        # ← copy this
          y: 5.678        # ← copy this
        orientation:
          z: 0.707        # ← copy this
          w: 0.707        # ← copy this

4. Repeat for each waypoint (3–5 waypoints recommended).

.. note::

   Orientation is a quaternion. For a 2D car, only ``z`` and ``w`` matter — just copy them directly from the echo output. You do not need to convert to/from degrees.

Steps
-----

1️⃣ Create the Package
^^^^^^^^^^^^^^^^^^^^^^^^

On the robot, navigate to your workspace and create a new package:

.. code-block:: bash

   cd ~/f1tenth_ws/src
   ros2 pkg create waypoint_nav --build-type ament_python --dependencies rclpy nav2_msgs geometry_msgs

This creates a ``waypoint_nav`` package with the necessary Nav2 and geometry message dependencies.

2️⃣ Create the Python Node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open the node file:

.. code-block:: bash

   code ~/f1tenth_ws/src/waypoint_nav/waypoint_nav/waypoint_nav_client.py

Paste the following code:

.. code-block:: python

   import rclpy
   from rclpy.action import ActionClient
   from rclpy.node import Node
   from nav2_msgs.action import NavigateThroughPoses
   from geometry_msgs.msg import PoseStamped


   class WaypointNavClient(Node):
       def __init__(self):
           super().__init__('waypoint_nav_client')
           self._client = ActionClient(
               self, NavigateThroughPoses, 'navigate_through_poses')

       def create_pose(self, x, y, oz=0.0, ow=1.0):
           """Create a PoseStamped in the map frame."""
           pose = PoseStamped()
           pose.header.frame_id = 'map'
           pose.header.stamp = self.get_clock().now().to_msg()
           pose.pose.position.x = x
           pose.pose.position.y = y
           pose.pose.orientation.z = oz
           pose.pose.orientation.w = ow
           return pose

       def send_waypoints(self):
           self.get_logger().info('Waiting for NavigateThroughPoses action server...')
           self._client.wait_for_server()
           self.get_logger().info('Action server available.')

           goal = NavigateThroughPoses.Goal()

           # ============================================================
           # REPLACE THESE WITH YOUR OWN MAP COORDINATES
           # Use "ros2 topic echo /goal_pose" to get coordinates
           # ============================================================
           goal.poses = [
               self.create_pose(1.0, 0.5, 0.0, 1.0),
               self.create_pose(2.0, 1.0, 0.707, 0.707),
               self.create_pose(1.0, 2.0, 1.0, 0.0),
           ]

           self.get_logger().info(f'Sending {len(goal.poses)} waypoints...')
           future = self._client.send_goal_async(
               goal, feedback_callback=self.feedback_callback)
           future.add_done_callback(self.goal_response_callback)

       def goal_response_callback(self, future):
           goal_handle = future.result()
           if not goal_handle.accepted:
               self.get_logger().error('Goal rejected by Nav2')
               return
           self.get_logger().info('Goal accepted — navigating...')
           result_future = goal_handle.get_result_async()
           result_future.add_done_callback(self.result_callback)

       def feedback_callback(self, feedback_msg):
           current = feedback_msg.feedback.current_pose.pose.position
           remaining = feedback_msg.feedback.number_of_poses_remaining
           self.get_logger().info(
               f'Poses remaining: {remaining}  |  '
               f'Current position: ({current.x:.2f}, {current.y:.2f})')

       def result_callback(self, future):
           status = future.result().status
           if status == 4:
               self.get_logger().info('Navigation complete!')
           else:
               self.get_logger().warn(f'Navigation finished with status: {status}')
           rclpy.shutdown()


   def main():
       rclpy.init()
       node = WaypointNavClient()
       node.send_waypoints()
       rclpy.spin(node)

.. important::

   The example coordinates above are placeholders. You **must** replace them with coordinates from your own map using the echo method described above.

3️⃣ Update setup.py
^^^^^^^^^^^^^^^^^^^^^

Open the package's ``setup.py``:

.. code-block:: bash

   code ~/f1tenth_ws/src/waypoint_nav/setup.py

Add the node to the ``console_scripts`` entry point:

.. code-block:: python

   entry_points={
       'console_scripts': [
           'waypoint_nav_client = waypoint_nav.waypoint_nav_client:main',
       ],
   },

4️⃣ Build and Source
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cd ~/f1tenth_ws
   colcon build --packages-select waypoint_nav
   source install/setup.bash

5️⃣ Start Bringup (Terminal 1)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Make sure the PlayStation controller is connected to the car, then open a terminal on the robot and run:

.. code-block:: bash

   bringup

This calls ``ros2 launch f1tenth_stack bringup_launch.py``, which starts the car's sensors and drivers.

.. note::

   If Nav2 later reports ``Timed out waiting for transform from base_link to odom``, the PlayStation controller is likely not connected. The VESC driver requires the joystick to fully initialize, and without it the ``odom`` frame is never published.

.. warning::

   **Hold R1 for autonomous mode.** By default the joystick continuously publishes zero-speed commands at high priority, blocking Nav2. Hold **R1** (button 5) on the PlayStation controller to enable autonomous mode — this lets Nav2's drive commands through. Releasing R1 returns to manual joystick control.

Leave this terminal running.

6️⃣ Launch Nav2 (Terminal 2)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open a **new** terminal and source the workspace:

.. code-block:: bash

   cd ~/f1tenth_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash

Launch the full Nav2 stack:

.. code-block:: bash

   ros2 launch f1tenth_stack nav2_launch.py map_name:=hallway_map

Leave this terminal running.

7️⃣ Open RViz2 and Set Initial Pose (Terminal 3)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open a new terminal on the robot and launch RViz2:

.. code-block:: bash

   source /opt/ros/humble/setup.bash
   rviz2

- Add a **Map** display (Topic: ``/map``, Durability Policy: ``Transient Local``)
- Add **Path** displays for ``/plan`` and ``/local_plan`` to visualize the planned route
- Click **2D Pose Estimate** in the toolbar and set the car's position and heading on the map

8️⃣ Run the Waypoint Navigation Client (Terminal 4)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open a **new** terminal, source the workspace, and run the node:

.. code-block:: bash

   cd ~/f1tenth_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ros2 run waypoint_nav waypoint_nav_client

You should see output like:

.. code-block:: text

   [INFO] [waypoint_nav_client]: Waiting for NavigateThroughPoses action server...
   [INFO] [waypoint_nav_client]: Action server available.
   [INFO] [waypoint_nav_client]: Sending 3 waypoints...
   [INFO] [waypoint_nav_client]: Goal accepted — navigating...
   [INFO] [waypoint_nav_client]: Poses remaining: 2  |  Current position: (0.85, 0.42)
   [INFO] [waypoint_nav_client]: Poses remaining: 1  |  Current position: (1.93, 0.98)
   [INFO] [waypoint_nav_client]: Navigation complete!

.. warning::

   **Hold R1** on the PlayStation controller throughout the entire navigation run. Releasing R1 stops Nav2's commands from reaching the wheels.

9️⃣ Watch the Car Navigate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- The global planner computes a path through all waypoints
- The controller follows the path in real time — watch the ``/plan`` and ``/local_plan`` displays update in RViz2
- Unlike the RViz2 GUI waypoint method, ``NavigateThroughPoses`` plans a continuous path through the poses without stopping at each one
- The node exits automatically when navigation completes

.. note::

   If the car does not move after running the node, confirm that:

   - You set the initial pose with **2D Pose Estimate** (step 7️⃣)
   - You are holding **R1** on the PlayStation controller
   - Nav2 lifecycle nodes are all active (check ``ros2 node list``)
   - The action server is available (check ``ros2 action list`` — you should see ``/navigate_through_poses``)
   - Your waypoint coordinates are reachable on the map (not inside walls or outside the costmap)

Topics and Actions
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Topic / Action
     - Type
     - Description
   * - ``/navigate_through_poses``
     - ``nav2_msgs/action/NavigateThroughPoses``
     - Action server — accepts a list of poses and navigates through them
   * - ``/plan``
     - ``nav_msgs/Path``
     - Global path planned by Nav2
   * - ``/local_plan``
     - ``nav_msgs/Path``
     - Local path the controller is currently following
   * - ``/cmd_vel``
     - ``geometry_msgs/Twist``
     - Velocity commands sent to the car by the controller
