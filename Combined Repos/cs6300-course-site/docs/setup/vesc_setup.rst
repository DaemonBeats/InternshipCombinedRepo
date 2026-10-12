.. _doc_vesc_setup:

VESC setup
==========

This page describes how to set up a VESC (Voltage Electronic Speed Controller) for RoboRacer vehicles.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

A short overview of the VESC and its role in the RoboRacer stack.

Requirements
------------

- VESC-compatible ESC hardware
- USB-to-serial adapter (if needed)
- `VESC Tool` or other flashing/configuration software

1. udev Rules Setup
--------------------

When you connect the VESC to the Jetson, the operating system will assign it a device name of the form ``/dev/ttyACMx``, where ``x`` is a number that depends on the order in which devices were plugged in. For example, if you plug in the lidar before the VESC, the lidar will be assigned ``/dev/ttyACM0`` and the VESC will be assigned ``/dev/ttyACM1``.

This is a problem because the car's configuration needs to know the device name for the VESC, and it can change every time the Jetson reboots depending on initialization order.

Fortunately, Linux has a utility named **udev** that allows us to assign each device a "virtual" name based on its vendor and product IDs. For example, we can configure udev so the VESC is always accessible as ``/dev/sensors/vesc``, regardless of initialization order.

Setting Up the VESC udev Rule
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo nano /etc/udev/rules.d/99-vesc.rules

.. code-block:: text

   KERNEL=="ttyACM[0-9]*", ACTION=="add", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0666", GROUP="dialout", SYMLINK+="sensors/vesc"

.. note::

   This rule matches any device that connects on a ``/dev/ttyACMx`` port with the VESC vendor ID (``0483``) and product ID (``5740``), and creates a persistent symlink at ``/dev/sensors/vesc``.

Activating the Rules
~~~~~~~~~~~~~~~~~~~~~

After saving the file, trigger (activate) the new rules by running:

.. code-block:: bash

   sudo udevadm control --reload-rules
   sudo udevadm trigger

Verifying the Setup
~~~~~~~~~~~~~~~~~~~~

Reboot your system, then verify the VESC device is correctly mapped by running:

.. code-block:: bash

   ls /dev/sensors

You should see ``vesc`` listed in the output.

.. tip::

   If you don't know the vendor or product ID of a device, you can find it by running ``lsusb`` after plugging in the device. Look for the entry matching your device — the ID is shown in the format ``XXXX:YYYY`` where ``XXXX`` is the vendor ID and ``YYYY`` is the product ID.


