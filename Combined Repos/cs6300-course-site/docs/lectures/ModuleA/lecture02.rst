.. _doc_lecture02:


Lecture 2 - Automatic Emergency Braking
==========================================

**Overview:** 
	This lecture goes over the importance of safety when working with autonomous systems. When is a system "safe enough" to deploy? In this lecture, you will learn about how Automatic Emergency Braking (AEB) works in today's vehicle as well as methods for gathering information about the outside world in order for the vehicle to respond to it appropriately. Once the vehicle has acquired real world data and reacts to its situation accordingly, how do we measure how "safe" the reaction is?

**Topics Covered:**
	-	Autonomatic Emergency Braking (AEB)
	-	Range Sensors for Autonomous Vehicles
	-	Working with Laser Scan Data
	-	Notions of Correctness


**Associated Tutorial:**
	.. toctree::
	   :maxdepth: 1
	   :name: sec-tutorial2

	   tutorial2

**Associated Assignment:** 
	* :ref:`Lab 2: Automatic Emergency Braking <doc_lab2>`

**Slides:**

	.. raw:: html

		<iframe width="700" height="500" src="https://docs.google.com/presentation/d/1HQSLPLE-fZ3EN-9PyqMd7-ti7JSLKL7qlrouGFEprU0/embed?start=false&loop=false&delayms=60000" frameborder="0" width="960" height="569" allowfullscreen="true" mozallowfullscreen="true" webkitallowfullscreen="true"></iframe>
		
**Video:**

	.. raw:: html

		<iframe width="700" height="500" src="https://www.youtube.com/embed/k4FQ-dZ0Lp8" title="RoboRacer L02 - Automatic Emergency Braking" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

.. <iframe width="560" height="315" src="https://www.youtube.com/embed/zkMelEB3-PY" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

.. **Links to additional resources:**
	- `RoboRacer Simulator Repo <https://github.com/f1tenth/f110_ros/tree/master/f110_simulator>`_

	Automatic Emergency Braking
===========================

Automatic Emergency Braking (AEB)
---------------------------------

Automatic Emergency Braking (AEB) is a safety feature available in many modern vehicles. It's designed to detect an impending collision and, if necessary, apply the brakes to prevent or reduce the severity of a crash.

How does it work?
~~~~~~~~~~~~~~~~~

AEB systems use sensors, cameras, radar, and lidar technology to monitor the vehicle's surroundings and detect potential obstacles. When the system determines that a collision is imminent:

#. It alerts the driver with audible and visual warnings.
#. If the driver doesn't take action promptly, the system can automatically apply the brakes.

Nissan AEB
~~~~~~~~~~

.. image:: https://img.youtube.com/vi/OyfPrEnAwdg/sddefault.jpg
   :alt: Watch the Nissan AEB video
   :target: https://youtu.be/OyfPrEnAwdg

Benefits
~~~~~~~~

- **Safety**: AEB can help prevent accidents or reduce their severity, thus protecting passengers, drivers, and pedestrians.
- **Reduced Driver Stress**: It serves as an extra set of eyes, providing an additional layer of security.
- **Potential Insurance Savings**: Some insurance companies offer discounts for vehicles equipped with AEB.

.. figure:: media/radar_vision.jpg
   :align: center
   :width: 100%
   :alt: radar vision

   Radar Calibrated Vision Pipeline - Binary Classifier

Limitations
~~~~~~~~~~~

- **Sensor Limitations**: AEB might not detect obstacles if the sensors are dirty or covered.
- **Weather Conditions**: Heavy rain, fog, or snow can reduce the system's effectiveness.
- **No Replacement for Driver Vigilance**: AEB is a supplemental system, and drivers should always be attentive and ready to take control.

.. figure:: media/truth_table.jpg
   :align: center
   :width: 70%
   :alt: Truth Table

   Classifications

Future of AEB
~~~~~~~~~~~~~

With advancements in AI and sensor technology, the efficiency and reliability of AEB systems are expected to improve. They may also integrate with other vehicle systems for a more holistic safety approach, such as connecting with vehicle-to-vehicle (V2V) communication systems.

AEB Videos
~~~~~~~~~~

.. image:: https://img.youtube.com/vi/815fsWXerIg/sddefault.jpg
   :alt: Watch AEB video 1
   :target: https://youtu.be/815fsWXerIg

.. image:: https://img.youtube.com/vi/bUhFfunT2ds/sddefault.jpg
   :alt: Watch AEB video 2
   :target: https://youtu.be/bUhFfunT2ds

Tesla Crash in China
~~~~~~~~~~~~~~~~~~~~

.. image:: https://img.youtube.com/vi/fc0yYJ8-Dyo/sddefault.jpg
   :alt: Watch Tesla crash video
   :target: https://youtu.be/fc0yYJ8-Dyo

Uber Self Driving Car Crash
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://img.youtube.com/vi/NJeQ0Dj4jAE/sddefault.jpg
   :alt: Watch Uber self-driving crash video
   :target: https://youtu.be/NJeQ0Dj4jAE


NTSB Report Summary: Uber Autonomous Vehicle Crash in Tempe, Arizona
-------------------------------------------------------------------

Background
~~~~~~~~~~

- **Date:** March 18, 2018
- **Location:** Tempe, Arizona
- **Incident:** An autonomous test vehicle operated by Uber struck and killed a pedestrian.

Key Findings
~~~~~~~~~~~~

#. **Vehicle's Perception System:**

   - The vehicle's radar and LIDAR sensors detected the pedestrian 6 seconds before the impact.
   - However, the system did not classify her as a pedestrian, because she was crossing a street at a location without a crosswalk.
   - The system struggled to predict her path, considering her as an unknown object, a vehicle, and then as a bicycle, leading to delays in the decision-making process.

#. **Emergency Braking:**

   - The self-driving system was designed not to initiate emergency braking on its own.
   - It relied on the human backup driver to intervene. However, the system did not alert the driver to do so.

#. **Backup Driver:**

   - The driver was found to be distracted and not watching the road.
   - The interior camera showed the driver was looking down at a personal device multiple times before the crash.
   - The NTSB highlighted the inadequacy of Uber's oversight in ensuring drivers followed company policies on attentiveness.

#. **Pedestrian Behavior:**

   - The pedestrian was found to have methamphetamine and marijuana in her system, which could have impaired her ability to judge the distance and speed of the oncoming vehicle.
   - She did not look in the direction of the vehicle until just before impact.

#. **Recommendations:**

   - Stronger guidelines for the testing of autonomous vehicles on public roads.
   - Better oversight of backup drivers to ensure attentiveness.
   - Enhanced safety systems that can initiate emergency braking when needed, without relying solely on human intervention.

.. image:: media/vehicle_stop_distance_side.png
   :alt: side view stopping

.. image:: media/vehicle_stop_distance_front.png
   :alt: vehicle view stopping


Euclidean Distance vs Time to Collision
---------------------------------------

#. **Euclidean Distance:**
   Euclidean distance is the straight-line distance between two points in Euclidean space. It's the most common way to calculate the "ordinary" distance between two points.

#. **Time to Collision (TTC):**
   TTC is a measure of time. Specifically, it estimates the amount of time it will take for two objects to collide if they continue on their current trajectories at their current speeds. The formula for TTC can be based on the range-rate, which is the rate at which the distance between the two objects is changing.

Comparison
~~~~~~~~~~

Nature
^^^^^^

- Euclidean distance is a spatial metric that quantifies the "separation" between two points in space.
- TTC is a temporal metric that quantifies the "separation" in time before a potential collision.

Units
^^^^^

- Euclidean distance is typically measured in spatial units like meters, kilometers, etc.
- TTC is measured in time units like seconds.

Application
^^^^^^^^^^^

- Euclidean distance is commonly used in geometry, computer graphics, machine learning (for clustering, classification, etc.), and many other fields.
- TTC is specifically used in safety-critical applications like collision avoidance systems in vehicles, drones, and other moving platforms.

Interdependence
^^^^^^^^^^^^^^^

While they are distinct concepts, they can be related. For example, if you know the Euclidean distance between two moving objects and their relative velocity, you can compute the TTC. Conversely, if you know the TTC and the relative velocity, you can infer the Euclidean distance at which the objects will collide if no actions are taken.

In summary, while both Euclidean distance and TTC can provide insights into the relationship between two entities (points or objects), one is spatial, and the other is temporal. They are used in different contexts but can be interconnected in applications like collision avoidance.


Time to Collision (TTC)
-----------------------

"Time to Collision" (TTC) is a measure used in traffic safety to estimate the time it will take for two objects (usually vehicles) to collide if they continue on their current paths at their current speeds. It's a useful metric, especially for driver assistance systems and autonomous vehicles, to evaluate the safety of a given traffic scenario.

.. figure:: media/TTC_Calculation.jpg
   :align: center
   :width: 70%
   :alt: TTC

   Time To Collision (TTC)

If the two objects are moving directly towards each other, :math:`\Delta v` is simply the sum of their velocities. If they are moving in the same direction, :math:`\Delta v` is the difference in their velocities.

Example
~~~~~~~

Consider two cars:

- Car A is stationary.
- Car B is moving towards Car A at a speed of 20 m/s.
- The distance between them is 100 meters.

Given the scenario, the TTC is:

.. figure:: media/ttc_example.jpg
   :align: center
   :width: 70%
   :alt: TTC Example

   Time To Collision (TTC) Example

It means that if Car B continues at its current speed without slowing down or changing its path, it will collide with Car A in 5 seconds.

.. note::

   The above calculation assumes constant speeds and straight-line paths. In real-world scenarios where speeds and directions can change, the calculation becomes more complex. Advanced driver assistance systems and autonomous vehicles use sophisticated algorithms and sensors to estimate TTC in dynamic environments.


Time to Collision using laser data
----------------------------------

Let's break it down:

#. Suppose you have two objects: Object A (e.g., your vehicle) and Object B (e.g., another vehicle or obstacle).
#. Let :math:`V` be the relative velocity of Object A with respect to Object B.
#. Let :math:`\theta` be the angle between the direction of :math:`V` and the line-of-sight (direct path) between Object A and Object B.

The component of :math:`V` that is directly along the line-of-sight is given by :math:`V\cos(\theta)`. This component is called the **range-rate**, and it represents how fast the distance between the two objects is changing.

Time to Collision (TTC) using :math:`V\cos(\theta)`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given:

- :math:`R`: Current distance between Object A and Object B.
- Range-rate: :math:`\dot{R} = V\cos(\theta)`

The TTC can be calculated as:

.. figure:: media/range-rate.png
   :align: center
   :width: 70%
   :alt: range rate

   Time To Collision (TTC) Range Rate

.. note::

   This formula allows you to compute the time it will take for Object A to reach Object B (or vice versa) based on their relative velocity and the angle of approach. Again, it assumes that both objects continue on their current paths at their current speeds without any changes.


Planar Lidar
------------

A planar LiDAR (Light Detection and Ranging) is a device that uses laser light to measure distances to objects in a 2-dimensional plane. It operates by sending out laser beams and then measuring the time it takes for the light to be reflected back to the sensor.

Here's a breakdown of how a planar LiDAR is used to detect the distance to an object:

#. **Emission of Laser Beams:**

   - The LiDAR emits a laser beam in a specific direction.
   - The beam travels outward until it encounters an obstacle or object and gets reflected back.

   .. figure:: media/planarlidar.png
      :align: center
      :width: 70%
      :alt: planarlidar

      Planar Lidar (RPILidar laserscan)

#. **Detection of Reflected Light:**

   - A detector in the LiDAR system captures the reflected light.
   - The time between the emission of the laser pulse and the detection of the reflected light is recorded.

#. **Distance Calculation:**

   The speed of light is constant. Given this, the distance to the object can be determined using the formula:

   .. figure:: media/distance_calc.png
      :align: center
      :width: 20%
      :alt: distance calc

      Distance to Object Calculation

   Where:

   - :math:`c` = speed of light (approximately :math:`3 \times 10^8` meters per second)
   - :math:`t` = time taken for the laser beam to travel to the object and back
   - The division by 2 accounts for the round-trip distance (to the object and back).

#. **Scanning Mechanism:**

   - While the basic principle described above gets the distance to a single point, a planar LiDAR typically has a mechanism to rotate or oscillate the laser emitter and detector assembly.
   - This allows the LiDAR to scan its surroundings in a planar fashion, generating a 2D "map" of distances at various angles.
   - The result is typically called a "scan" or "profile", which is a set of distance values corresponding to various angles around the LiDAR.

#. **Data Interpretation:**

   - The raw data from the LiDAR can be processed to detect objects, measure their distance, and determine their shape (at least in the plane of the LiDAR's scan).
   - Algorithms can be applied to segment this data, distinguishing between different objects, and even estimating the size or orientation of detected objects.

   .. figure:: media/lidar_measurements.png
      :align: center
      :width: 70%
      :alt: lidar measurements

      This image shows the different variables stored in the Turtlebot4 LaserScan messages

   .. figure:: media/interface_scan.png
      :align: center
      :width: 70%
      :alt: interface scan

      Stored values for LaserScan message for Turtlebot4

   **Key Data:**

   - ``angle_min``: radians
   - ``angle_max``: radians
   - ``angle_increment``: radians
   - ``ranges``: meters

   .. figure:: media/info_scan.png
      :align: center
      :width: 70%
      :alt: info scan

      Example scan message fields

   .. figure:: media/echoscan.png
      :align: center
      :width: 70%
      :alt: echo scan

      Example scan message output

   - Example: angle increment :math:`0.000184629` radians = ~ 0.5 degrees

Applications
~~~~~~~~~~~~

- Planar LiDARs are commonly used in robotics for obstacle detection and navigation.
- They're also used in certain autonomous vehicle systems, especially in scenarios where 2D profiling is adequate.
- Industries utilize planar LiDARs for safety systems, ensuring that machinery or automated platforms do not collide with obstacles.

Advantages and Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Advantages**: Planar LiDARs are typically simpler and less expensive than their 3D counterparts. They provide accurate distance measurements and can work in a variety of lighting conditions, including darkness.
- **Limitations**: They only capture data in a single plane, so they might miss obstacles that lie above or below this plane. For a more comprehensive understanding of the environment, 3D LiDAR systems or multiple planar LiDARs at different orientations might be required.

In summary, a planar LiDAR is a powerful tool for distance measurement and object detection in a 2D plane, with applications ranging from robotics to industrial safety systems.

Hokuyo UST-10LX 2D LiDAR
------------------------

`Manufacturer website <https://hokuyo-usa.com/products/lidar-obstacle-detection/ust-10lx>`_

.. figure:: media/10XL.PNG
   :align: center
   :alt: UST-10LX

   UST-10LX

Hokuyo UST-10LX Key Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Measurement Range
^^^^^^^^^^^^^^^^^^^^

- **Maximum Range**: 10 meters
- **Minimum Range**: 0.06 meters (60 mm)

2. Field of View (FoV)
^^^^^^^^^^^^^^^^^^^^^^

- **270° field of view**, ideal for wide-angle scanning.

3. Accuracy
^^^^^^^^^^^

- **±30 mm** accuracy under standard conditions.

4. Angular Resolution
^^^^^^^^^^^^^^^^^^^^^

- **0.25°** resolution for precise measurement.

5. Scanning Frequency
^^^^^^^^^^^^^^^^^^^^^

- **40 Hz** scanning speed for fast updates.

6. Light Resistance
^^^^^^^^^^^^^^^^^^^

- Operates in environments with **ambient light up to 100,000 lux**.

7. Communication
^^^^^^^^^^^^^^^

- **Ethernet interface** for high-speed data transfer.

8. Power Requirements
^^^^^^^^^^^^^^^^^^^^

- Operates on **12V DC**.
- **Typical Power Consumption**: ~8W.

9. Size and Weight
^^^^^^^^^^^^^^^^^^

- **Compact and lightweight**:

  - Dimensions: **62 × 62 × 87 mm**
  - Weight: **130 g**

10. Environmental Durability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **IP65-rated** enclosure for dustproof and water-resistant operation.

11. Applications
^^^^^^^^^^^^^^^^

- Perfect for:

  - Indoor robotics and navigation
  - Warehouse automation
  - SLAM-based mapping systems