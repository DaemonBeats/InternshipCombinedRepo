.. _doc_roboracer_stack:

=====================
RoboRacer Driver Stack
=====================

Create a workspace
==================

.. code-block:: bash

   cd $HOME
   mkdir -p f1tenth_ws/src


Move to workspace
=================

.. code-block:: bash

   cd f1tenth_ws
   colcon build


Clone the repo
==============

.. code-block:: bash

   cd src
   git clone https://github.com/Weber-AGV/f1tenth_system


Update submodule
================

.. code-block:: bash

   cd f1tenth_system
   git submodule update --init --force --remote


Change branches to Humble
=========================

.. code-block:: bash

   git switch humble-devel
   cd teleop_tools
   git switch humble-devel
   cd ..
   cd vesc
   git switch humble


Install dependencies
====================

.. code-block:: bash

   cd $HOME/f1tenth_ws
   sudo rosdep init

.. code-block:: bash

   rosdep update


Install missing dependencies
=============================

Ensure the missing ``asio_cmake_module`` dependency is installed. Use ``rosdep`` to install all necessary dependencies for the ``vesc_driver`` package:

.. code-block:: bash

   rosdep install --from-paths src --ignore-src -r -y


Check your ROS 2 installation
==============================

Verify that the required ROS 2 packages (``io_context`` and ``asio_cmake_module``) are installed:

.. code-block:: bash

   sudo apt update && sudo apt install ros-humble-io-context ros-humble-asio-cmake-module


Build
=====

.. code-block:: bash

   colcon build --symlink-install
   source ~/.bashrc
