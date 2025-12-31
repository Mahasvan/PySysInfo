Classes
=======

-----------------
Hardware Managers
-----------------

Depending on the OS present, PySysInfo can automatically load one of the following Hardware Manager classes.
All these classes implement the structure in :class:`pysysinfo.models.info_models.HardwareManagerInterface`.

.. autoclass:: pysysinfo.models.info_models.HardwareManagerInterface
    :members:

.. autoclass:: pysysinfo.dumps.windows.windows_dump.WindowsHardwareManager
    :show-inheritance:


-------------
Hardware Info
-------------
Objects of this type store the retrieved data in their HardwareManager.

.. autoclass:: pysysinfo.models.info_models.HardwareInfo
    :exclude-members: __new__,__init__,model_config
    :members:

Each OS implements its own HardwareInfo class. As of the latest version, they have no difference in their structure.

.. autoclass:: pysysinfo.models.info_models.WindowsHardwareInfo
    :show-inheritance:
    :exclude-members: __new__,__init__

.. autoclass:: pysysinfo.models.info_models.MacHardwareInfo
    :show-inheritance:
    :exclude-members: __new__,__init__

.. autoclass:: pysysinfo.models.info_models.LinuxHardwareInfo
    :show-inheritance:
    :exclude-members: __new__,__init__

- `WindowsHardwareManager`: Implements `HardwareManagerInterface` and pulls CPU, memory, storage, and graphics data via Windows Registry and WMI helpers. See [src/pysysinfo/dumps/windows/windows_dump.py](src/pysysinfo/dumps/windows/windows_dump.py#L14-L49).
- `MacHardwareManager`: Uses `sysctl` and IORegistry helpers to populate platform models. See [src/pysysinfo/dumps/mac/mac_dump.py](src/pysysinfo/dumps/mac/mac_dump.py#L14-L49).
- `LinuxHardwareManager`: Reads sysfs-driven helpers to build the Linux hardware snapshot. See [src/pysysinfo/dumps/linux/linux_dump.py](src/pysysinfo/dumps/linux/linux_dump.py#L12-L49).

The top-level `HardwareManager` alias in [src/pysysinfo/__init__.py](src/pysysinfo/__init__.py#L1-L14) selects one of the managers above based on the current platform, so user code can depend on a single interface.
