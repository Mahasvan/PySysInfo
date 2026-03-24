# HWProbe

A Python Library to simplify retrieval of hardware components of your computer.

- To get started, read the **[Quickstart](https://mahasvan.github.io/HWProbe/quickstart.html).**
- Additionally, you can view the **[Documentation](https://mahasvan.github.io/HWProbe/)**.

## Installation

### macOS / Linux

```bash
pip3 install HWProbe
```

### Windows

```bash
pip install HWProbe
```

## Usage

```python
from hwprobe import HardwareManager
import json

hm = HardwareManager()

data = hm.fetch_hardware_info()

# All data returned are Pydantic models and have strict schema
# You can use it as is, or serialize it to JSON if you wish.
# We print the data in JSON here for readability.

json_data = json.loads(data.model_dump_json())
print(json.dumps(json_data, indent=2))
```

<details>

<summary>Sample Output</summary>


```json
{
  "cpu": {
    "status": {
      "type": "success",
      "messages": []
    },
    "name": "Apple M3 Pro",
    "architecture": "ARM",
    "bitness": 64,
    "arch_version": "8",
    "vendor": "Apple",
    "sse_flags": [],
    "cores": 12,
    "threads": 12
  },
  "memory": {
    "status": {
      "type": "success",
      "messages": [
        "ARM macOS only exposes partial RAM data."
      ]
    },
    "modules": [
      {
        "manufacturer": "Micron",
        "part_number": null,
        "type": "LPDDR5",
        "capacity": {
          "capacity": 18,
          "unit": "GB"
        },
        "frequency_mhz": null,
        "slot": null,
        "supports_ecc": null,
        "ecc_type": null
      }
    ]
  },
  "storage": {
    "status": {
      "type": "success",
      "messages": []
    },
    "modules": [
      {
        "model": "APPLE SSD AP0512Z",
        "manufacturer": "Apple",
        "identifier": "disk0",
        "location": "Internal",
        "connector": "Apple Fabric",
        "type": "Solid State Drive (SSD)",
        "vendor_id": null,
        "device_id": null,
        "size": {
          "capacity": 477102,
          "unit": "MB"
        }
      },
      {
        "model": "Built In SDXC Reader",
        "manufacturer": "Apple",
        "identifier": null,
        "location": "Internal",
        "connector": "Secure Digital",
        "type": "Unknown",
        "vendor_id": null,
        "device_id": null,
        "size": null
      }
    ]
  },
  "graphics": {
    "status": {
      "type": "success",
      "messages": []
    },
    "modules": [
      {
        "name": "Apple M3 Pro",
        "vendor_id": "0x106b",
        "device_id": null,
        "manufacturer": "Apple Inc.",
        "subsystem_manufacturer": null,
        "subsystem_model": null,
        "acpi_path": null,
        "pci_path": null,
        "pcie_width": null,
        "pcie_gen": null,
        "vram": {
          "capacity": 18432,
          "unit": "MB"
        },
        "apple_gpu_info": {
          "gpu_core_count": 20,
          "performance_shader_count": 8,
          "gpu_gen": 15
        }
      }
    ]
  },
  "network": {
    "status": {
      "type": "success",
      "messages": []
    },
    "modules": [
      {
        "name": "Ethernet Adapter (en4)",
        "device_id": null,
        "vendor_id": null,
        "acpi_path": null,
        "pci_path": null,
        "manufacturer": null,
        "interface": "en4",
        "mac_address": "XX:XX:XX:XX:XX:XX",
        "type": "Ethernet",
        "ip_address": null
      },
      {
        "name": "Wi-Fi",
        "device_id": "0x4434",
        "vendor_id": "0x14e4",
        "acpi_path": null,
        "pci_path": null,
        "manufacturer": "Apple",
        "interface": "en0",
        "mac_address": "XX:XX:XX:XX:XX:XX",
        "type": "AirPort",
        "ip_address": "10.200.185.18"
      }
    ]
  }
}
```

</details>

## Tracker

### Hardware Discovery Progress Tracker

| Component   | Linux | macOS  | Windows |
|-------------|:-----:|:------:|:-------:|
| CPU         |   ✅   |   ✅    |    ✅    |
| GPU         |   ✅   |   ✅    |    ✅    |
| Memory      |   ✅   |   ✅    |    ✅    |
| Network     |   ✅   |   ✅    |    ✅    |
| Storage     |   ✅   |   ✅    |    ✅    | 
| --          |  --   |   -    |    -    |
| Display     |   ❌   | ❌* (1) | ✅* (2)  |
| Audio       |   ❌   |   ❌    | ✅* (2)  |
| Motherboard |   ❌   |   ❌    |    ✅    |
| Vendor      |   ❌   |   ❌    |    ➖    |
| Input       |   ❌   |   ❌    |    ❌    |


1. In progress
2. Need to rewrite C++ bindings (In progress)

### Miscellaneous Tasks / Problems

| Task                                                                                             | Status |
|--------------------------------------------------------------------------------------------------|:------:|
| GH actions for compiling `interops/{platform}/*.{c\|cpp}` to their respective output directories |   ✅    |
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
