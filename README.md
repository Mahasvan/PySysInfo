# PySysInfo

A Python Library to simplify retrieval of hardware components of your computer.

- To get started, read the **[Quickstart](https://mahasvan.github.io/PySysInfo/quickstart.html).**
- Additionally, you can view the **[Documentation](https://mahasvan.github.io/PySysInfo/)**.


## Installation

### macOS / Linux

```bash
pip3 install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ PySysInfo
```

### Windows

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ PySysInfo
```

## Usage

```python
from pysysinfo import HardwareManager
import json

hm = HardwareManager()

data = hm.fetch_hardware_info()

# All data returned are Pydantic models and have strict schema
# You can use it as is, or serialize it to JSON if you wish.
# We print the data in JSON here for readability.

json_data = json.loads(data.model_dump_json())
print(json.dumps(json_data, indent=2))
```

## Tracker

### Hardware Discovery Progress Tracker

| Component   | Linux | macOS  | Windows |
|-------------|:-----:|:------:|:-------:|
| CPU         |   ✅   |   ✅    |    ✅    |
| GPU         |   ✅   |   ✅    | ✅* (1)  |
| Memory      |   ✅   |   ✅    |    ✅    |
| Network     |   ❌   |   ✅    |    ✅    |
| Audio       |   ❌   |   ❌    |    ✅    |
| Motherboard |   ❌   |   ❌    |    ✅    |
| Storage     |   ✅   |   ✅    |    ✅    |
| Display     |   ❌   | ❌* (2) | ✅* (3)  |
| Vendor      |   ❌   |   ❌    |    ➖    |
| Input       |   ❌   |   ❌    |    ❌    |

1. PCIe gen info only for Nvidia
2. In progress
3. Need to rewrite C++ bindings

### Miscellaneous Tasks / Problems

| Task                                                                                             | Status |
|--------------------------------------------------------------------------------------------------|:------:|
| GH actions for compiling `interops/{platform}/*.{c\|cpp}` to their respective output directories |   ❌    |
| Group Pydantic Model fields into essential and optional                                          |   ❌    |
| Remove `pyobjc` dependency in macOS by rewriting dependent code chunks in C++                    |   ✅    |
| Autodetection of storage units                                                                   |   ❌    |

### Supporting Features

| Feature                                                                                                                      | Status |
|------------------------------------------------------------------------------------------------------------------------------|:------:|
| PCI Lookup — [DeviceHunt](https://devicehunt.com)                                                                            |   ❌    |
| PCI Lookup — [PCI IDs Repository](https://pci-ids.ucw.cz) ([GitHub](https://github.com/pciutils/pciids/blob/master/pci.ids)) |   ❌    |
| Logging                                                                                                                      |   ✅    |
| Working Library                                                                                                              |   ✅    |
