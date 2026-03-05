# PySysInfo

A Python Library to simplify retrieval of hardware components of your computer.

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
### Miscellaneous Tasks / Problems

- [ ] Implement GH actions for compiling modules from `interops/{platform}/*.{c|cpp}` to their respective output
  directories
- [ ] Group Pydantic Model fields into essential and optional. 
- [x] Remove `pyobjc` dependency in macOS by rewriting dependent code chunks in C++ 
- [ ] Autodetection of storage units

### Hardware Discovery

- Linux
    - [x] CPU
    - [x] GPU
    - [x] Memory
    - [ ] Network
    - [ ] Audio
    - [ ] Motherboard
    - [ ] Input
    - [x] Storage
- macOS
    - [x] CPU
    - [x] GPU
    - [x] Memory
    - [x] Network - _Make faster? Wifi info is slow to fetch_
    - [ ] Audio
    - [ ] Vendor
    - [ ] Input
    - [x] Storage
    - [ ] Display
- Windows
    - [x] CPU
    - [x] GPU - _PCIe gen info only for Nvidia GPUs_
    - [x] Memory
    - [x] Network
    - [x] Audio
    - [x] Motherboard
    - [ ] Input
    - [x] Storage
    - [x] Display - Revamp the C++ Lib

### Supporting Features

- [ ] PCI Lookup - DeviceHunt
- [ ] PCI
  Lookup - [PCI IDs Repository](https://pci-ids.ucw.cz) - [GitHub](https://github.com/pciutils/pciids/blob/master/pci.ids)
- [x] Logging
- [x] Working Library
