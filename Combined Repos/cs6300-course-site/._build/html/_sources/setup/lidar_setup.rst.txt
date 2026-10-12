.. _doc_lidar_setup:

Lidar Setup
===========

.. contents:: Table of Contents
   :local:
   :depth: 2

1️⃣ Create a New Network Connection
------------------------------------

Run the following command to create a connection named ``Hokuyo`` for the ``enP8p1s0`` interface:

.. code-block:: bash

   sudo nmcli connection add type ethernet con-name Hokuyo ifname enP8p1s0 ipv4.addresses 192.168.0.15/24 ipv4.gateway 192.168.0.10 ipv4.method manual

This sets:

- **IP address**: ``192.168.0.15``
- **Subnet mask**: ``/24`` (equivalent to ``255.255.255.0``)
- **Gateway**: ``192.168.0.10``
- **Manual IP configuration** (not DHCP)

2️⃣ Verify the Connection
--------------------------

List all available connections to confirm the ``Hokuyo`` connection was created:

.. code-block:: bash

   nmcli connection show

You should see an entry for ``Hokuyo``.

3️⃣ Activate the Connection
-----------------------------

Activate the newly created ``Hokuyo`` connection:

.. code-block:: bash

   sudo nmcli connection up Hokuyo

This enables the configuration for the ``enP8p1s0`` interface.

4️⃣ Verify the Network Configuration
--------------------------------------

Check that the ``enP8p1s0`` interface has the correct settings:

.. code-block:: bash

   ip addr show enP8p1s0

You should see the IP address ``192.168.0.15`` assigned to the interface.

5️⃣ Test the Connection
------------------------

Ping the Hokuyo LiDAR at ``192.168.0.10`` to confirm connectivity:

.. code-block:: bash

   ping 192.168.0.10

6️⃣ Create an Alias for Quick Lidar Ping
-----------------------------------------

Add the following alias to your ``~/.bashrc`` for a quick shortcut to ping the LiDAR:

.. code-block:: bash

   alias lidar="ping 192.168.0.10"

Then reload your shell configuration:

.. code-block:: bash

   source ~/.bashrc

Now you can test the LiDAR connection anytime by simply typing ``lidar`` in the terminal.
