# PySysInfo

A Python Library to simplify retrieval of hardware components of your computer.

## Installation

### macOS / Linux
```bash
git clone https://github.com/mahasvan/pysysinfo
cd pysysinfo
pip3 install build
python3 -m build
pip3 install -e .
```
### Windows
```bash
git clone https://github.com/mahasvan/pysysinfo
cd pysysinfo
pip install build
python -m build
pip install -e .
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
  - [x] GPU* [could get more info than what is currently discovered]
  - [x] Memory
  - [ ] Network
  - [ ] Audio
  - [ ] Vendor
  - [ ] Input
  - [x] Storage
  - [ ] Display
- Windows
  - [x] CPU
  - [x] GPU* [PCIe gen info only for Nvidia GPUs]
  - [x] Memory
  - [ ] Network
  - [ ] Audio
  - [ ] Motherboard
  - [ ] Input
  - [x] Storage

### Supporting Features

- [ ] PCI Lookup - DeviceHunt
- [ ] PCI Lookup - [PCI IDs Repository](https://pci-ids.ucw.cz) - [GitHub](https://github.com/pciutils/pciids/blob/master/pci.ids)
- [x] Logging
- [x] Working Library
