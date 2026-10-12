.. _doc_info_realsense_d435i:


INSTALL - Realsense D435i
==================================


1. Jetson Orin Kernel Builder
-----------------------------

`jetson-orin-kernel-builder <https://github.com/jetsonhacks/jetson-orin-kernel-builder>`_

Tools to build the Linux kernel and modules on board the Jetson AGX Orin, Orin Nano, or Orin NX. This tool is designed for beginning to intermediate users. Be sure to read the entire document in the repository before proceeding.

.. code-block:: bash

   git clone https://github.com/jetsonhacks/jetson-orin-kernel-builder.git
   cd jetson-orin-kernel-builder


Getting Kernel and Module Sources
---------------------------------

Run the following from the repository root to fetch the kernel and module sources:

.. code-block:: bash

   ./scripts/get_kernel_sources.sh


Editing the Kernel Configuration
--------------------------------

Edit the kernel-builder configuration using the provided GUI script:

.. code-block:: bash

   ./scripts/edit_config_gui.sh

You can use the GUI to set device and kernel options:

.. image:: media/kernel_config_gui.png
   :alt: Kernel configuration GUI
   :align: center
   :width: 600px


Searching for the CH341 Driver

Use **Ctrl+F** to search for **CH341**.

.. image:: media/search_ch341.png
   :alt: Search for CH341
   :align: center
   :width: 480px

Next, click the letter **N** to change it to **M** for the *CH341 Single Port Driver* so it is built as a module.

.. image:: media/ch341_to_module.png
   :alt: Set CH341 to Module (M)
   :align: center
   :width: 480px

Use **Ctrl+F** to search for **HID_SENSOR_HUB**.

.. image:: media/hid_sensor_hub_to_m.png
   :alt: Search for HID_SENSOR_HUB
   :align: center
   :width: 600px

Next, click the letter **N** to change it to **M** for the *HID Sensors framework support* so it is built as a module.

Use **Ctrl+F** to search for **ACCEL_3D**.

.. image:: media/accel_3d_to_m.png
   :alt: Search for HID_SENSOR_HUB
   :align: center
   :width: 600px

Next, click the letter **N** to change it to **M** for the *HID Accelerometers 3D* so it is built as a module.

Use **Ctrl+F** to search for **GYRO_3D**.

.. image:: media/gyro_3d_to_m.png
   :alt: Search for HID_SENSOR_HUB
   :align: center
   :width: 600px

Next, click the letter **N** to change it to **M** for the *HID Gyroscope 3D* so it is built as a module.


When finished, save and quit the configuration editor to apply the change.




Building the Kernel Image
-------------------------

Run the kernel build and module installation scripts from the repository.  
This step may take up to **30 minutes**.

.. code-block:: bash

   ./scripts/make_kernel.sh

Copy the path to the generated kernel image. You will need it later

.. image:: media/path_to_image.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Next, you will edit the build_info.txt file 

.. code-block:: bash
    
    gedit build_info.txt

Edit the document to include the path to the kernel image you copied earlier.

.. image:: media/gedit_build_info.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Building the Kernel Modules
-------------------------

Build the kernel modules using the provided script.

.. code-block:: bash

   ./scripts/make_kernel_modules.sh


When prompted Do you want to install the modules? Type **N** and press Enter.

Installing a New Modules
-------------------------

Run this script to get Module information.

.. code-block:: bash

   ./scripts/module_info.sh -s CH34

Look for the module name **ch341** and see if it is in the right location:

.. image:: media/CH341_module_name.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Using the module location make sure it is in there:

.. code-block:: bash

    ls /usr/src/kernel/kernel-jammy-src/drivers/usb/serial/ch341.ko

Output should be something like this:

.. image:: media/ch341_module_ko_found.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

More detailed information about the module by running:

.. code-block:: bash

   ./scripts/module_info.sh CONFIG_USB_SERIAL_CH341

.. image:: media/ch341_module_deep.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Copy the ch341 module to the current directory: (Make sure to use the correct path you found when you located the module earlier)

.. code-block:: bash

    cp /usr/src/kernel/kernel-jammy-src/drivers/usb/serial/ch341.ko .

Create an install module script:

.. code-block:: bash

    ./scripts/install_module_author.sh ch341 drivers/usb/serial

Use the script to install the module (type 'y' when prompted):

.. code-block:: bash

    ./install_module_ch341.sh

Output should be something like this:

.. image:: media/install_output.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

verify the module is installed:

.. code-block:: bash

    lsmod | grep ch341

Output should be something like this:

.. image:: media/verify_install.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Installing the Kernel Image
-------------------------

Run the following script to install the kernel image:

Make a backup of your current kernel image:

.. code-block:: bash

    cd /boot/extlinux/
    sudo cp extlinux.conf extlinux.conf.original

Edit the file:

.. code-block:: bash

    sudo gedit extlinux.conf

Make a backup copy of the Image (use a new terminal window):

.. code-block:: bash

    cd /boot
    sudo cp Image Image.backup

Go back to the extlinux.conf file and unccomment the Label Backup lines:

Pre-Edit

.. image:: media/config_pre_edit.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Post-Edit

.. image:: media/config_post_edit.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Copy line 10 and replace line 29 like the image below :

.. image:: media/config_append_change.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

When complete Save and close the file

Go back to jetson-orin-kernel-builder directory:

.. code-block:: bash

    cd ~/jetson-orin-kernel-builder

Copy the kernel image:

.. code-block:: bash

    sudo cp /usr/src/kernel/kernel-jammy-src/arch/arm64/boot/Image /boot/Image

Reboot your Jetson:


JetPack 6 Orin Kernel Builder Video Walkthrough
---------------------------

This process applies to **JetPack 6**. A supporting walkthrough video is available on YouTube.

.. raw:: html

   <div class="video-container">
       <iframe width="560" height="315"
               src="https://www.youtube.com/embed/7P6I2jeJNYo"
               title="Jetson Orin Kernel Builder — YouTube"
               frameborder="0"
               allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
               referrerpolicy="strict-origin-when-cross-origin"
               allowfullscreen>
       </iframe>
   </div>

2. Jetson Orin helper: JetsonHacks `jetson-orin-librealsense <https://github.com/jetsonhacks/jetson-orin-librealsense>`_

   Clone the JetsonHacks helper repository and follow its README for Jetson-specific build and install instructions:

   .. code-block:: bash

       git clone https://github.com/jetsonhacks/jetson-orin-librealsense.git
       cd jetson-orin-librealsense/build

Run this patch

.. code-block:: bash

   ./patch-for-realsense.sh


Build the Modules:
-----------------

Switch over to the kernel building directory:

.. code-block:: bash

   cd ~/jetson-orin-kernel-builder/


Run the script to install the modules:

.. code-block:: bash

   ./scripts/make_kernel_modules.sh

When prompted Do you want to install the modules? Type **N** and press Enter.

Complete a checksum:

.. code-block:: bash

   cd ~/jetson-orin-librealsense/
   sha256sum -c install-modules.tar.gz.sha256

The checksum should look something like this:

.. image:: media/checksum.png
   :alt: Kernel build output path
   :align: center
   :width: 600px

Expand and install modules directory:

.. code-block:: bash

   tar -xzf install-modules.tar.gz
   cd install-modules

Run the install script :

.. code-block:: bash

   sudo ./install-realsense-modules.sh

Install librealsense
--------------------

Register the Intel RealSense public key:

.. code-block:: bash

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE || sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE


Add the server to the list of repositories:

.. code-block:: bash

    sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" -u

Install the RealSense SDK 2.0:

.. code-block:: bash

    sudo apt-get install librealsense2-utils
    sudo apt-get install librealsense2-dev

With the installation complete, reconnect the RealSense device:

.. code-block:: bash

    realsense-viewer

Update the camera firmware to the latest version:

.. image:: media/update_firmware.png
   :alt: Kernel build output path
   :align: center
   :width: 600px



Other Resources
-------------------- 

Installing Intel RealSense SDK 2.0: `Jetson Hacks install Intel RealSense <https://jetsonhacks.com/2025/03/20/jetson-orin-realsense-in-5-minutes/>`_

Product page: `Intel RealSense D435i <https://www.realsenseai.com/products/depth-camera-d435i/>`_

Getting started: `RealSense developer docs <https://dev.realsenseai.com/docs/docs-get-started>`_

.. raw:: html

    <div class="video-container">
        <iframe width="560" height="315" src="https://www.youtube.com/embed/FpMCJsg_KmE?si=qhhzguxsaBv_YG6D" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </div> 