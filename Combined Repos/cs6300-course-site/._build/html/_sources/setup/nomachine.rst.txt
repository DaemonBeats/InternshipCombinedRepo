.. _doc_nomachine:

========================
NoMachine
========================


Install NoMachine on RoboRacer
==============================

.. code-block:: bash

   wget https://www.nomachine.com/free/arm/v8/deb -O nomachine.deb


Install using dpkg
------------------

.. code-block:: bash

   sudo dpkg -i nomachine.deb


Documentation
-------------

See the official NoMachine documentation:
`https://kb.nomachine.com/AR02R01074 <https://kb.nomachine.com/AR02R01074>`_


Install NoMachine on Host Machine (Ubuntu)
==========================================

Download NoMachine for Ubuntu:
`https://downloads.nomachine.com/download/?id=1 <https://downloads.nomachine.com/download/?id=1>`_


Install using dpkg
------------------

.. code-block:: bash

   cd ~/Downloads
   sudo dpkg -i nomachine_8.16.1_1_amd64.deb


Connect to RoboRacer
====================

On the host machine, open **NoMachine**.


Add a new connection
--------------------

Click on the **Add** button.

.. image:: media/add_comp.png
   :alt: Add computer in NoMachine
   :align: center


Configure the connection
------------------------

- Add the name of the bot  
- Add the IP address of the bot  
- Check **Always accept the host's verification**  
- Click **Add**

.. image:: media/add_name.png
   :alt: Add RoboRacer connection details
   :align: center


Select the RoboRacer
--------------------

Find the bot in the list of computers and select it.

.. image:: media/load.png
   :alt: Select RoboRacer from list
   :align: center


Enter credentials
-----------------

Enter the credentials for the RoboRacer.

.. image:: media/credentials.png
   :alt: RoboRacer login credentials
   :align: center


Connected
---------

You should now be connected to the RoboRacer desktop.

.. image:: media/connected.png
   :alt: Connected RoboRacer desktop
   :align: center
