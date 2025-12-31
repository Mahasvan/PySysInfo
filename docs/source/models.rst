Models
======

PySysInfo exposes Pydantic models for each hardware subsystem plus shared helpers for capacity units and discovery status.

Component Models
----------------
.. autoclass:: pysysinfo.models.cpu_models.CPUInfo
    :members:
    :undoc-members:
    :show-inheritance:

- ``GraphicsInfo``
- ``GPUInfo``
- ``MemoryInfo``
- ``MemoryModuleInfo``
- ``MemoryModuleSlot``
- ``StorageInfo``
- ``DiskInfo``

Capacities
----------
- ``Kilobyte``: Storage size in KB. See [src/pysysinfo/models/size_models.py](src/pysysinfo/models/size_models.py#L9-L11).
- ``Megabyte``: Storage size in MB. See [src/pysysinfo/models/size_models.py](src/pysysinfo/models/size_models.py#L14-L16).
- ``Gigabyte``: Storage size in GB. See [src/pysysinfo/models/size_models.py](src/pysysinfo/models/size_models.py#L19-L21).

Statuses
--------
- ``SuccessStatus``: Marks successful discovery for a component. See [src/pysysinfo/models/status_models.py](src/pysysinfo/models/status_models.py#L11-L13).
- ``PartialStatus``: Signals partial discovery with accumulated messages. See [src/pysysinfo/models/status_models.py](src/pysysinfo/models/status_models.py#L16-L21).
- ``FailedStatus``: Denotes failure to collect data, preserving one or more error messages. See [src/pysysinfo/models/status_models.py](src/pysysinfo/models/status_models.py#L24-L44).
