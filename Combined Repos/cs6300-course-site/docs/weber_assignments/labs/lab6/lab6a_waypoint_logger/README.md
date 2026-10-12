# Lab 6a - Waypoint Logger for Pure Pursuit

## I. Learning Goals

- Create a ROS 2 Python package from scratch
- Subscribe to a localization topic and extract pose data
- Write pose data to a CSV file in real time
- Understand how the particle filter provides map-relative position
- Prepare waypoint data for the Pure Pursuit algorithm

## II. Overview

In the Pure Pursuit pipeline, the car needs a pre-recorded path to follow. That path is a CSV file of poses (x, y, heading) captured while you manually drive the track. In this lab you will build the **waypoint logger node** that records those poses.

The particle filter publishes the car's estimated position on the map at ~30-40 Hz on `/pf/pose/odom`. Your node will subscribe to that topic and append each pose to a CSV file. The resulting file will be used in the next lab (Pure Pursuit) to drive the car autonomously.

| Part | Task | What You Learn |
|------|------|----------------|
| 1 | Create the `pure_pursuit` package | ROS 2 package structure, `ament_python`, dependencies |
| 2 | Write the waypoint logger node | Subscriptions, Odometry messages, CSV file I/O |
| 3 | Record a lap of waypoints | Running nodes, particle filter localization, data collection |
| 4 | Verify and visualize the waypoints | Data validation, CSV inspection |

## III. Prerequisites

- Completed **Lab 5** (SLAM and Nav2 — you have a saved map)
- Particle filter configured and working (see the Particle Filter tutorial)
- Comfortable creating files and editing Python on the robot

## IV. Part 1 — Create the Package

Create a new ROS 2 Python package on the robot:

```bash
cd ~/f1tenth_ws/src
ros2 pkg create pure_pursuit --build-type ament_python --dependencies rclpy nav_msgs geometry_msgs
```

Create a directory for your waypoint CSV files:

```bash
mkdir -p ~/f1tenth_ws/src/pure_pursuit/maps
```

## V. Part 2 — Write the Waypoint Logger Node

Create the file `pure_pursuit/pure_pursuit/waypoint_logger.py`. Your node must:

1. **Subscribe** to `/pf/pose/odom` (message type: `nav_msgs/msg/Odometry`)
2. **Open a CSV file** for writing when the node starts (save to `~/f1tenth_ws/src/pure_pursuit/maps/waypoints.csv`)
3. **In the callback**, extract the pose from each Odometry message and write a row to the CSV:
   - `x` — `msg.pose.pose.position.x`
   - `y` — `msg.pose.pose.position.y`
   - `z` — `msg.pose.pose.orientation.z` (quaternion z, used to reconstruct heading)
   - `w` — `msg.pose.pose.orientation.w` (quaternion w)
4. **Print a confirmation** so you know poses are being recorded (e.g., print every 50th pose to avoid flooding the terminal)
5. **Close the CSV file cleanly** when the node shuts down (Ctrl+C)

### Hints

- Use Python's built-in `csv` module or simply write comma-separated strings
- The CSV should have **no header row** — just the four values per line: `x, y, z, w`
- The Odometry message definition is in `nav_msgs.msg`. Import it with:

  ```python
  from nav_msgs.msg import Odometry
  ```

- To handle clean shutdown, close the file in a `try/finally` block or override `destroy_node()`

### Register the Entry Point

Edit `setup.py` in the `pure_pursuit` package. Add your node to the `console_scripts` list:

```python
entry_points={
    'console_scripts': [
        'waypoint_logger = pure_pursuit.waypoint_logger:main',
    ],
},
```

### Build

```bash
cd ~/f1tenth_ws
colcon build --packages-select pure_pursuit
source install/setup.bash
```

## VI. Part 3 — Record a Lap

1. Start **bringup** (Terminal 1)
2. Launch the **particle filter** (Terminal 2):

   ```bash
   cd ~/f1tenth_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ros2 launch particle_filter localize_launch.py
   ```

3. Open **RViz2** (Terminal 3) and set the **2D Pose Estimate** so the particle filter is localized. **The particle filter must be localized before you start recording** — if it is not, your waypoints will be meaningless
4. Run your **waypoint logger** (Terminal 4):

   ```bash
   cd ~/f1tenth_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ros2 run pure_pursuit waypoint_logger
   ```

5. Using the PlayStation controller, **drive a complete lap** of the track at a moderate, consistent speed
6. When you return to the starting position, press **Ctrl+C** to stop the logger

**Tips for a good recording:**

- Drive at the speed you want the car to follow autonomously later
- Cover the entire track — drive all sections at least once
- Close the loop — finish near where you started
- Avoid sharp jerks or corrections, as they will be recorded into the path

## VII. Part 4 — Verify the Recording

Check that your CSV was created and contains data:

```bash
wc -l ~/f1tenth_ws/src/pure_pursuit/maps/waypoints.csv
```

A full lap should produce **several hundred waypoints** (the particle filter publishes at ~30-40 Hz). If the count is very low, the particle filter may not have been localized — re-run with the initial pose set.

Inspect the first few lines:

```bash
head -5 ~/f1tenth_ws/src/pure_pursuit/maps/waypoints.csv
```

You should see four comma-separated numbers per line (x, y, orientation_z, orientation_w).

## VIII. Deliverables

| # | Deliverable | Points |
|---|-------------|--------|
| 1 | Screenshot of your `waypoint_logger.py` source code | 25 |
| 2 | Screenshot of the terminal showing the logger running and recording poses as you drive | 25 |
| 3 | The `waypoints.csv` file submitted to Canvas | 25 |
| 4 | Screenshot of `wc -l` and `head -5` output showing the CSV has several hundred rows of valid data | 25 |

**Total: 100 Points**
