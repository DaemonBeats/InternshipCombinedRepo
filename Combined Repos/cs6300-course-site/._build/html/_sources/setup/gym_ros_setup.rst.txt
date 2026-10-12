.. _doc_gym_ros_setup:

Gym_Ros Setup
=============

This page describes how to set up Gym ROS integration for RoboRacer.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

This page provides the steps required to set up the gym_ros simulator environment for RoboRacer. It will use Docker and foxglove to run the gym environment in a similar fashion over different OSes.

Requirements
------------

 - As Docker is being used, this setup is OS agnostic. It should work on Linux, Windows, and MacOS. The specs of the devices should not need to be too powerful to run the simulator. A modern laptop with 8GB of RAM and a quad-core CPU should be sufficient.
 - Go to foxglove.dev and create an account. You will need to log in to foxglove studio to view the gym_ros environment.

Windows setup
-------------

1️⃣ **Install Docker**

We will start by downloading Docker Desktop and getting it running. You can download Docker Desktop from the official website: https://docs.docker.com/desktop/setup/install/windows-install/

There are a few videos online that can help with the Docker installation process. Here's one: https://www.youtube.com/watch?v=TMx4ydYKCHw

*Important Note:* Things may not work starting from step 7 in the Windows section if you do not run the Docker Desktop app before running the commands in step 7. Make sure to run the Docker Desktop app first.

2️⃣ **Repo Setup**

Open a terminal and navigate to the directory where you want the repository to be cloned to. For my example, I will use C:\Users\Student\Documents>

Once you're in the directory, run the following command in the terminal:

.. code-block:: bash

   git clone https://github.com/f1tenth/f1tenth_gym_ros.git

Then, navigate to the newly created directory:

.. code-block:: bash
   cd f1tenth_gym_ros

You should now see your new directory path. For example, C:\Users\Student\Documents\f1tenth_gym_ros>
We will now swap to the dev-humble branch of the repository. Run the following command in the terminal:

.. code-block:: bash
   git checkout dev-humble
