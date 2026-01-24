Theory
======

PySysInfo standardizes OS-specific discovery into a shared `HardwareInfo` model. Each platform manager wraps a set of `fetch_*` helpers that pull from native sources and populate Pydantic models for CPU, memory, storage, and graphics.

Platform data sources
---------------------
- Linux: reads system facts from the sysfs pseudo file system via `fetch_*` helpers under `pysysinfo.dumps.linux`.
- Windows: queries the Registry and WMI through the helpers in `pysysinfo.dumps.windows`.
- macOS: uses `sysctl` and IORegistry via helpers in `pysysinfo.dumps.mac`.

Per-component collection (placeholder)
-------------------------------------------
The sections below outline where data comes from per component and platform. Detailed prose will follow; placeholder text is provided for now.

CPU
~~~
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Linux managers read processor facts from sysfs, Windows relies on WMI and Registry keys, and macOS uses `sysctl` output.

Memory
~~~~~~
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Memory discovery walks DIMM slots and capacity details using platform-native tools.

Storage
~~~~~~~
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Storage discovery aggregates block devices and metadata from each platform.

Graphics
~~~~~~~~
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Graphics adapters and VRAM sizing are gathered from the GPU helpers per platform.
