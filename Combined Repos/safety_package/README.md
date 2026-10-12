# safety_package

Automatic emergency braking (AEB) for an F1TENTH-style car. The node drives the
car forward at a fixed cruise speed and stops it when the time-to-collision
(TTC) with an obstacle ahead becomes too small.

The same node is provided in Python and in C++. They use the same node name
(`safety_node`), topics, parameters and logic, so **run only one at a time**.

| Implementation | Source                           | Executable        |
| -------------- | -------------------------------- | ----------------- |
| Python         | `safety_package/safety_node.py`  | `safety_node`     |
| C++            | `src/safety_node.cpp`            | `safety_node_cpp` |

## Build

The package must sit in the `src` folder of a ROS 2 workspace. The commands
below assume the workspace is `~/ros2_ws`; adjust the path to match yours.

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y   # install dependencies (first time only)
colcon build --packages-select safety_package
source install/setup.bash
```

One build produces both executables. Run `source install/setup.bash` in every
new terminal before using `ros2 run`.

If you built this package before the C++ node was added, remove the old build
output first:

```bash
rm -rf build/safety_package install/safety_package
```

## Run

### Python

```bash
ros2 run safety_package safety_node
```

### C++

```bash
ros2 run safety_package safety_node_cpp
```

The car will not move until messages are arriving on both `/scan` and `/odom`.
Until then the node holds the brake and prints a warning naming the missing
topic.

### Running in the simulator

The F1TENTH simulator publishes odometry on `/ego_racecar/odom` instead of
`/odom`, so remap the topic:

```bash
ros2 run safety_package safety_node --ros-args -r /odom:=/ego_racecar/odom
ros2 run safety_package safety_node_cpp --ros-args -r /odom:=/ego_racecar/odom
```

## Topics

| Topic    | Type                                    | Direction |
| -------- | --------------------------------------- | --------- |
| `/scan`  | `sensor_msgs/msg/LaserScan`             | Subscribe |
| `/odom`  | `nav_msgs/msg/Odometry`                 | Subscribe |
| `/drive` | `ackermann_msgs/msg/AckermannDriveStamped` | Publish |

## Parameters

Both implementations accept the same parameters.

| Parameter            | Default | Unit | Meaning                                                       |
| -------------------- | ------- | ---- | ------------------------------------------------------------- |
| `ttc_threshold`      | 0.5     | s    | Brake when the TTC drops below this.                          |
| `release_distance`   | 1.0     | m    | The front cone must be clear this far to release the brake.   |
| `release_cone_angle` | 20.0    | deg  | Half-width of the front cone checked for release.             |
| `sensor_timeout`     | 0.25    | s    | Brake if `/scan` or `/odom` is older than this.               |
| `cruise_speed`       | 1.0     | m/s  | Speed commanded while the path is clear.                      |

Set them on the command line with `-p`. Values must be written as decimals
(`2.0`, not `2`):

```bash
ros2 run safety_package safety_node --ros-args -p ttc_threshold:=0.8 -p cruise_speed:=2.0
ros2 run safety_package safety_node_cpp --ros-args -p ttc_threshold:=0.8 -p cruise_speed:=2.0
```

## How it works

1. **TTC:** for every valid LiDAR beam, `TTC = range / (speed * cos(angle))`.
   Only beams the car is moving toward are counted.
2. **Brake:** when the smallest TTC falls below `ttc_threshold`, the brake
   latches and a stop command is published immediately.
3. **Release:** the brake stays on until the car has stopped and nothing is
   within `release_distance` in the front cone.
4. **Watchdog:** if `/scan` or `/odom` goes quiet for longer than
   `sensor_timeout`, the node commands a stop until data returns.

Only forward motion is protected; reversing never triggers the brake.
