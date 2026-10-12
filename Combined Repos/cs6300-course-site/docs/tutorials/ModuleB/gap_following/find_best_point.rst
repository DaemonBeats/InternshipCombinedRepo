.. _doc_tutorials_find_best_point:

Finding the Best Point: Naive Selection
=========================================

After detecting the maximum gap, we need to **pick a specific point** within that gap to steer toward.

The simplest approach is the **Naive Selection** method — picking the **farthest point closest to the center** of the gap.

Why This Approach?
------------------

- The **farthest point** in the gap gives the robot the most room to maneuver.
- Picking the **center** of the gap avoids steering too close to either side of obstacles.
- Simple and computationally efficient — no complex prediction or planning needed.

Step-by-Step Breakdown
-----------------------

1️⃣ **Extract the Gap**
   After finding the start and end indices of the maximum gap, we isolate just that portion of the LiDAR scan.

2️⃣ **Find the Farthest Point**
   Within the gap, find the point with the **maximum distance** — this is the safest direction.

3️⃣ **Convert to Steering Angle**
   Convert the LiDAR index of the farthest point into a steering angle using the angle increment.

4️⃣ **Publish Drive Command**
   Send the steering angle to the vehicle's Ackermann drive controller.

Python Implementation
---------------------

.. code-block:: python

   def find_best_point(self, ranges, start_idx, end_idx):
       """
       Select the best point within the largest gap to aim toward.

       Strategy: Pick the point with the maximum distance (farthest point)
       within the gap, ideally close to the center.

       Args:
           ranges (np.array): Processed LiDAR data
           start_idx (int): Starting index of the gap
           end_idx (int): Ending index of the gap

       Returns:
           best_point_idx (int): Index of the selected steering point
       """
       # Extract the subset of ranges within the gap
       gap_ranges = ranges[start_idx:end_idx + 1]

       # Find the index of the farthest point within the gap
       best_point_relative_idx = np.argmax(gap_ranges)

       # Adjust to the actual index in the full LiDAR scan
       best_point_idx = start_idx + best_point_relative_idx

       return best_point_idx

Converting Index to Steering Angle
-----------------------------------

Once we have the best point index, we convert it to a steering angle:

.. code-block:: python

   def scan_callback(self, data: LaserScan):
       """
       Full callback integrating gap detection and steering.
       """
       ranges = data.ranges
       angle_increment = data.angle_increment

       # Step 1: Preprocess
       proc_ranges = self.preprocess_lidar(ranges)

       # Step 2: Apply safety bubble
       proc_ranges = self.create_safety_bubble(proc_ranges)

       # Step 3: Find maximum gap
       start_idx, end_idx = self.find_max_gap(proc_ranges)

       # Step 4: Find best point
       best_point_idx = self.find_best_point(proc_ranges, start_idx, end_idx)

       # Step 5: Calculate steering angle
       # The angle is calculated relative to the center of the scan
       center_idx = len(ranges) // 2
       steering_angle = (best_point_idx - center_idx) * angle_increment

       # Step 6: Publish drive command
       self.publish_drive_command(steering_angle, speed=1.5)

.. important::

   **Hokuyo Scan Is Flipped!**

   The Hokuyo UST-10LX LiDAR scan is **reversed** (index 0 is on the **right** side of the vehicle).

   This means we need to **negate the steering angle** to correct for the flip:

   .. code-block:: python

      steering_angle = -1.0 * (best_point_idx - center_idx) * angle_increment

   Without this correction, the vehicle will steer in the **opposite direction**!

Strengths of Naive Selection
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - ✅ Strengths
     - ❌ Weaknesses
   * - Simple and fast
     - Tunnel vision (only looks at current scan)
   * - Works well in open environments
     - No prediction or planning
   * - Easy to debug
     - Sensitive to noise
   * - Low computational cost
     - Can cause hard turns in tight spaces
   * - Good for educational purposes
     - Doesn't handle dynamic obstacles

Weaknesses and Limitations
---------------------------

1️⃣ **Tunnel Vision**
   The algorithm only considers the **current LiDAR scan** and doesn't look ahead or predict future obstacles.

2️⃣ **No Prediction**
   The robot doesn't anticipate how the environment will change as it moves forward.

3️⃣ **Noise Sensitivity**
   A single noisy LiDAR reading could cause the robot to steer toward a false opening.

4️⃣ **Hard Turns**
   In tight spaces, the robot might make aggressive steering corrections instead of smooth paths.

5️⃣ **No Dynamic Obstacle Handling**
   Moving obstacles are not tracked or predicted — the robot only reacts to their current position.

When to Use This Method
------------------------

The **Naive Selection** method works well for:

- Learning and understanding the basics of Follow-The-Gap
- Open race tracks with wide corridors
- Environments with mostly static obstacles
- Initial prototyping before implementing advanced methods

For more sophisticated navigation, consider:

- **Weighted selection** (favoring forward direction)
- **Trajectory prediction** (simulating future positions)
- **Dynamic window approach** (considering vehicle dynamics)
- **Model predictive control** (optimizing over a horizon)

Next Steps
----------

- Implement the ``find_best_point()`` function in your gap_follow_node.
- Test the naive selection method in simulation.
- Tune the bubble radius and speed parameters for smooth navigation.
- Experiment with alternative selection strategies for improved performance.
