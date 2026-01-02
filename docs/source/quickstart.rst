Quickstart
==========

Prerequisites
-------------
- Python 3.9 or newer.
- On macOS, `pyobjc` is required; it is installed automatically as a dependency.

Install
-------
Currently, the project is hosted on TestPyPI. To install, run:

.. code-block:: bash

   pip3 install -i https://test.pypi.org/simple/ PySysInfo

Basic usage
-----------
Instantiate the platform-aware manager and collect everything in one shot:

.. code-block:: python

   from pysysinfo import HardwareManager

   manager = HardwareManager()
   hardware = manager.fetch_hardware_info()
   print(hardware.model_dump_json(indent=2))

Targeted collection
-------------------
Fetch individual components when you only need one subsystem:

.. code-block:: python

   from pysysinfo import HardwareManager

   manager = HardwareManager()

   cpu = manager.fetch_cpu_info()
   memory = manager.fetch_memory_info()
   storage = manager.fetch_storage_info()
   graphics = manager.fetch_graphics_info()

Serialization
-------------
All component models are Pydantic models, so they support `.model_dump()` for dictionaries and `.model_dump_json()` for JSON-ready strings. 

Status fields indicate whether each subsystem succeeded, partially succeeded, or failed. Refer to :ref:`errors-during-hardware-discovery` for more information.
