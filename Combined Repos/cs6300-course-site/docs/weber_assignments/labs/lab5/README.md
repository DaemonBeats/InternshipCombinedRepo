# Lab 5 - SLAM and Nav2 Navigation

## I. Learning Goals

- Map an environment using SLAM Toolbox
- Understand occupancy grid maps (`.pgm` / `.yaml`)
- Localize the car on a saved map using AMCL
- Navigate autonomously using the Nav2 stack (2D Goal Pose and Waypoint Navigation)
- Send waypoints programmatically using a Python ROS 2 action client
- Understand the Nav2 command pipeline: planner → controller → cmd_vel → ackermann → drive

## II. Overview

In this lab you will use the RoboRacer to map the CAE hallway loop, save the map, and then use the Nav2 navigation stack to autonomously drive the car to goal poses on that map. This lab ties together SLAM (mapping), AMCL (localization), and Nav2 (path planning + control).

| Part | Task | What You Learn |
|------|------|----------------|
| 1 | Map the hallway with SLAM Toolbox | Occupancy grids, SLAM, map saving |
| 2 | Send a 2D Goal Pose | AMCL localization, Nav2 path planning, autonomous driving |
| 3 | Navigate through multiple waypoints | Waypoint sequencing, behavior trees, Nav2 panel |
| 4 | Send waypoints programmatically | ROS 2 action clients, NavigateThroughPoses, Python nodes |

## III. Prerequisites

Before starting this lab, make sure you have:

- Completed the **SLAM tutorial** (you know how to drive, save, and verify a map)
- Completed the **Nav2 setup** (Nav2 packages installed, parameters file, launch file, and converter node created)

## IV. Part 1 — Map the Environment

Use SLAM Toolbox to create a map of the CAE hallway loop.

1. Connect the PlayStation controller and start **bringup** on the car.
2. Launch **SLAM Toolbox** in a second terminal.
3. Open **RViz2** and drive the car through the entire hallway loop using the joystick. Make sure the loop is closed.
4. Save the map:

   ```bash
   mkdir -p ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/maps
   ros2 run nav2_map_server map_saver_cli -f ~/f1tenth_ws/src/f1tenth_system/f1tenth_stack/maps/lab_map
   ```

5. Verify the files exist (`lab_map.pgm` and `lab_map.yaml`).
6. Rebuild the workspace so Nav2 can find the map:

   ```bash
   cd ~/f1tenth_ws
   colcon build --packages-select f1tenth_stack
   source install/setup.bash
   ```

7. **Verify** the map loads correctly by running the standalone map server and checking it in RViz2 (see the SLAM tutorial for detailed steps).

> **Tip:** Refer to the Saving the Map tutorial in the course documentation for the full step-by-step walkthrough if needed.

## V. Part 2 — 2D Goal Pose Navigation

Use Nav2 to send the car to a single goal on the map.

1. Close any running SLAM, map server, or RViz2 processes from Part 1. Start fresh.
2. Start **bringup** (Terminal 1):

   ```bash
   bringup
   ```

3. Launch **Nav2** (Terminal 2):

   ```bash
   cd ~/f1tenth_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ```

   If your map is saved as `lab_map` (the default):

   ```bash
   ros2 launch f1tenth_stack nav2_launch.py
   ```

   To load a different map:

   ```bash
   ros2 launch f1tenth_stack nav2_launch.py map_name:=hallway_map
   ```

4. Open **RViz2** (Terminal 3) and add the following displays:
   - **Map** — Topic: `/map`, Durability Policy: `Transient Local`
   - **ParticleCloud** — Click **Add** → **By display type** → expand `nav2_rviz_plugins` → select **ParticleCloud**. Set Topic to `/particle_cloud` and Reliability Policy to `Best Effort`
   - **Map** (costmap) — Topic: `/global_costmap/costmap`, Color Scheme: `costmap`
   - **Polygon** (robot footprint) — Topic: `/global_costmap/published_footprint`
   - **Path** — Topic: `/plan` (global plan)
   - **Path** — Topic: `/local_plan` (controller's tracking path)
   - **MarkerArray** — Topic: `/waypoints`

5. Set the **2D Pose Estimate** — click the button in RViz2 and place the arrow at the car's actual position and orientation on the map. Watch the AMCL particle cloud converge around the car.
6. Set a **2D Goal Pose** — click the button and place a goal on the map.

> **⚠️ Hold R1 on the PlayStation controller** while the car is driving autonomously. Releasing R1 returns to manual joystick control and stops Nav2's commands from reaching the wheels.

7. Watch the car plan a path (green line in RViz2) and drive to the goal.
8. Send at least **3 different goals** to different locations on the map.

> **Tip:** Refer to the 2D Goal Pose tutorial in the course documentation for the full walkthrough.

## VI. Part 3 — Waypoint Navigation

Use Nav2's Navigate Through Poses to send the car through multiple waypoints in sequence.

1. With bringup and Nav2 still running, open the **Nav2 panel** in RViz2 (Panels → Add New Panel → `nav2_rviz_plugins/Nav2 Panel`).
2. Set the **2D Pose Estimate** if not already set.
3. Add the **Nav2 Goal** tool — click the **+** button in the RViz2 toolbar (next to 2D Goal Pose), select **GoalTool** under `nav2_rviz_plugins`, click OK.
4. Click the **Waypoint / Nav Through Poses Mode** button in the Nav2 panel.
5. Use the **Nav2 Goal** tool to click multiple points on the map to queue up waypoints.
6. Click **Start Nav Through Poses** in the Nav2 panel.

> **⚠️ Hold R1** throughout the entire waypoint sequence. If you release R1 mid-run, the car stops and Nav2 may report a controller failure.

7. Create a route of at least **5 waypoints** that makes the car drive a loop through the hallway.

> **Tip:** Refer to the Navigate Through Poses tutorial in the course documentation for the full walkthrough.

## VII. Part 4 — Programmatic Waypoint Navigation

Send waypoints to Nav2 from a Python node instead of clicking in RViz2.

1. Create a new package on the robot:

   ```bash
   cd ~/f1tenth_ws/src
   ros2 pkg create waypoint_nav --build-type ament_python --dependencies rclpy nav2_msgs geometry_msgs
   ```

2. Create the waypoint navigation client node at `waypoint_nav/waypoint_nav/waypoint_nav_client.py` using the code from the Programmatic Waypoint Navigation tutorial.
3. Update `setup.py` to add the `waypoint_nav_client` entry point.
4. Build the package:

   ```bash
   cd ~/f1tenth_ws
   colcon build --packages-select waypoint_nav
   source install/setup.bash
   ```

5. Get waypoint coordinates for your map — run `ros2 topic echo /goal_pose` and click **2D Goal Pose** in RViz2 at each desired location. Copy the x, y, orientation.z, and orientation.w values into your node.
6. With bringup, Nav2, and RViz2 running (and initial pose set), run your node:

   ```bash
   ros2 run waypoint_nav waypoint_nav_client
   ```

7. Hold **R1** and watch the car navigate through your waypoints.

> **Tip:** Refer to the Programmatic Waypoint Navigation tutorial in the course documentation for the full walkthrough.

## VIII. Deliverables

| # | Deliverable | Points |
|---|-------------|--------|
| 1 | Map files (`lab_map.pgm` and `lab_map.yaml`) submitted to Canvas | 20 |
| 2 | Screenshot of RViz2 showing the loaded map with AMCL particle cloud after setting the initial pose | 20 |
| 3 | Video: 2D Goal Pose — car navigating to a goal on the map (screen recording of RViz2 showing path + car movement) | 20 |
| 4 | Video: Waypoint Navigation — car following a 5+ waypoint route through the hallway (screen recording of RViz2) | 20 |
| 5 | Video: Programmatic Waypoints — car navigating through waypoints sent by your Python node (screen recording of RViz2 + terminal output) | 20 |

**Total: 100 Points**
