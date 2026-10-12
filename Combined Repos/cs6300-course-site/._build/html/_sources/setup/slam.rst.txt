.. _doc_setup_slam:

SETUP - SLAM
==================================

Install SLAM Toolbox
--------------------

1️⃣ **Install the SLAM Toolbox package**

.. code-block:: console

   sudo apt update
   sudo apt install ros-humble-slam-toolbox

.. note::

   If you get an apt lock error mentioning ``packagekitd``, stop it and try again:

   .. code-block:: console

      sudo systemctl stop packagekit
      sudo systemctl disable packagekit
      sudo apt update
      sudo apt install -y ros-humble-slam-toolbox



2️⃣ **Add an alias to your `~/.bashrc` to launch SLAM Toolbox**

.. note::

   Modify the path below for the specific robot you are using.
   This example is for ``f1-wsu-4``.

.. code-block:: console

   alias slam='ros2 launch slam_toolbox online_async_launch.py slam_params_file:=/home/f1-wsu-4/f1tenth_ws/src/f1tenth_system/f1tenth_stack/config/f1tenth_online_async.yaml'

After editing ``~/.bashrc``:

.. code-block:: console

   source ~/.bashrc

Open a new terminal to verify the alias works.

Install pip (Required for rosdep)
----------------------------------

Some dependencies require ``pip`` to be installed.

1️⃣ Install pip

.. code-block:: console

   sudo apt update
   sudo apt install -y python3-pip

2️⃣ Verify pip installation

.. code-block:: console

   pip3 --version


Install Particle Filter (Localization)
---------------------------------------

1️⃣ **Clone the particle_filter package**

.. code-block:: console

   cd ~/f1tenth_ws/src
   git clone https://github.com/f1tenth/particle_filter.git


2️⃣ **Install workspace dependencies**

.. code-block:: console

   cd ~/f1tenth_ws
   rosdep install -r --from-paths src --ignore-src --rosdistro humble -y


3️⃣ **Rebuild the workspace**

.. code-block:: console

   cd ~/f1tenth_ws
   colcon build
   source install/setup.bash


Install range_libc
------------------

1️⃣ **Clone the repository**

.. code-block:: console

   cd ~/f1tenth_ws/src
   git clone https://github.com/f1tenth/range_libc.git


2️⃣ **Install Cython (required)**

.. code-block:: console

   sudo python3 -m pip install Cython




3️⃣ **Install range_libc with CUDA support**

.. code-block:: console

   cd range_libc/pywrapper
   sudo WITH_CUDA=ON python3 setup.py install


Fix: CUDA / range_libc Build Error
------------------------------------

If you encounter a CUDA compilation error when building ``range_libc`` on a Jetson Orin, use the following fix script.

1️⃣ Create the Script
^^^^^^^^^^^^^^^^^^^^^

Create the file ``~/f1tenth_ws/src/range_libc/fix_range_libc.sh``:

.. code-block:: bash

   nano ~/f1tenth_ws/src/range_libc/fix_range_libc.sh

Paste in the following script:

.. code-block:: bash

   #!/bin/bash
   # Fix and build range_libc with CUDA for Jetson Orin (sm_87)
   # Run from: ~/f1tenth_ws/src/range_libc/pywrapper/

   set -e

   if [ ! -f "setup.py" ]; then
       echo "ERROR: Run this script from range_libc/pywrapper/"
       echo "  cd ~/f1tenth_ws/src/range_libc/pywrapper && bash fix_range_libc.sh"
       exit 1
   fi

   echo "Patching setup.py..."

   # 1. Remove -march=native (nvcc doesn't support it)
   sed -i 's/"-march=native", //' setup.py

   # 2. Remove bogus gcc-8 flags (gcc-8 is not installed on these systems)
   sed -i '/gcc-8\|g++-8/d' setup.py

   # 3. Update CUDA arch from sm_62 (TX2) to sm_87 (Orin NX / Orin Nano)
   sed -i 's/-arch=sm_62/-arch=sm_87/' setup.py

   # 4. Fix _compile so non-.cu files are explicitly routed to gcc (not nvcc)
   python3 - <<'PYEOF'
   with open('setup.py', 'r') as f:
       content = f.read()

   old = (
       "        else:\n"
       "            postargs = extra_postargs['gcc']\n"
       "        # postargs = extra_postargs#['gcc']\n"
       "\n"
       "        super(obj, src, ext, cc_args, postargs, pp_opts)\n"
       "        # reset the default compiler_so, which we might have changed for cuda\n"
       "        self.compiler_so = default_compiler_so"
   )
   new = (
       "        else:\n"
       "            # explicitly reset to gcc for all non-.cu files\n"
       "            self.set_executable('compiler_so', default_compiler_so)\n"
       "            postargs = extra_postargs['gcc']\n"
       "\n"
       "        super(obj, src, ext, cc_args, postargs, pp_opts)\n"
       "        # reset the default compiler_so, which we might have changed for cuda\n"
       "        self.set_executable('compiler_so', default_compiler_so)"
   )

   if old in content:
       content = content.replace(old, new)
       with open('setup.py', 'w') as f:
           f.write(content)
       print("  [OK] Fixed _compile compiler routing")
   elif "set_executable('compiler_so', default_compiler_so)" in content:
       print("  [SKIP] _compile routing already fixed")
   else:
       print("  [WARN] Could not match _compile pattern - check setup.py manually")
   PYEOF

   echo "Building with CUDA (this takes a minute)..."
   sudo rm -rf build/
   sudo env WITH_CUDA=ON python3 setup.py install

   echo "Done! range_libc installed with CUDA support."

2️⃣ Make It Executable
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   chmod +x ~/f1tenth_ws/src/range_libc/fix_range_libc.sh

3️⃣ Run the Script
^^^^^^^^^^^^^^^^^^

Navigate to the ``pywrapper`` directory first, then run the script:

.. code-block:: bash

   cd ~/f1tenth_ws/src/range_libc/pywrapper
   bash ../fix_range_libc.sh

.. note::

   The script must be run from inside the ``pywrapper/`` directory — it checks for ``setup.py`` in the current folder and will exit with an error if not found.