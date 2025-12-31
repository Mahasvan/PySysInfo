.. PySysInfo documentation master file, created by
   sphinx-quickstart on Wed Dec 31 19:12:18 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Home
====

PySysInfo gathers CPU, memory, storage, and graphics details across Linux, macOS, and Windows into a single set of Pydantic models. The top-level `HardwareManager` picks the right platform manager at import time, so usage stays the same everywhere.

Highlights
----------
- Cross-platform: sysfs on Linux, Registry/WMI on Windows, sysctl and IORegistry on macOS.
- Unified data model: `HardwareInfo` bundles component models for easy serialization.
- Pluggable managers: `LinuxHardwareManager`, `MacHardwareManager`, and `WindowsHardwareManager` expose the same API.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   theory
   classes
   models
