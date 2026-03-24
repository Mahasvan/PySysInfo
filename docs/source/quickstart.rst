.. _quickstart:

Quickstart
==========

Prerequisites
-------------
- Python 3.9 or newer.
- On macOS, `pyobjc` is required; it is installed automatically as a dependency.

Install
-------
To install HWProbe, run:

.. code-block:: bash

   pip3 install HWProbe
   pip install HWProbe  # Windows users may need to use 'pip' instead of 'pip3'


Basic usage
-----------
Instantiate the platform-aware manager and collect everything in one shot:

.. code-block:: python

   from hwprobe import HardwareManager

   manager = HardwareManager()
   hardware = manager.fetch_hardware_info()
   print(hardware.model_dump_json(indent=2))

For the list of components supported, refer to :ref:`supported`.

Targeted collection
-------------------
Fetch individual components when you only need one subsystem:

.. code-block:: python

   from hwprobe import HardwareManager

   manager = HardwareManager()

   cpu = manager.fetch_cpu_info()
   memory = manager.fetch_memory_info()
   storage = manager.fetch_storage_info()
   graphics = manager.fetch_graphics_info()



==========

Next Section: :ref:`hardware-managers`.