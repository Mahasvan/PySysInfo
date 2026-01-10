import ctypes
import subprocess
from typing import List

from pysysinfo.dumps.windows.win_enum import MEMORY_TYPE
from pysysinfo.interops.win.api.signatures import GetWmiInfo
from pysysinfo.models.memory_models import (
    MemoryInfo,
    MemoryModuleInfo,
    MemoryModuleSlot,
)
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import StatusType


def fetch_wmi_cmdlet_memory_info() -> MemoryInfo:
    memory_info = MemoryInfo()

    # 256 bytes per property, 9 properties, 6 modules
    buf_size = 256 * 9 * 8
    buffer = ctypes.create_string_buffer(buf_size)

    GetWmiInfo(
        b"SELECT BankLabel, Capacity, Manufacturer, PartNumber, Speed, DeviceLocator, SMBIOSMemoryType, DataWidth, TotalWidth FROM Win32_PhysicalMemory",
        b"ROOT\\CIMV2",
        buffer,
        buf_size,
    )

    """
    `raw_data` is in the following format:
    BankLabel=...|Capacity=...|...
    BankLabel=...|Capacity=...|...
    ...
    
    Each module is separated by a newline; and for each module,
    its properties are separated by a '|' character
    """

    raw_data = buffer.value.decode("utf-8", errors="ignore")

    if not raw_data:
        memory_info.status.type = StatusType.FAILED
        memory_info.status.messages.append("WMI query returned no data")
        return memory_info

    for line in raw_data.split("\n"):
        if not line or "|" not in line:
            continue

        module = MemoryModuleInfo()
        unparsed = line.split("|")

        parsed_data = {
            x.split("=", 1)[0]: x.split("=", 1)[1] for x in unparsed if "=" in x
        }

        bank_label = parsed_data["BankLabel"]
        capacity = parsed_data["Capacity"]
        manufacturer = parsed_data["Manufacturer"]
        part_number = parsed_data["PartNumber"]
        speed = parsed_data["Speed"]
        device_locator = parsed_data["DeviceLocator"]
        smbios_mem_type = parsed_data["SMBIOSMemoryType"]
        data_width = parsed_data["DataWidth"]
        total_width = parsed_data["TotalWidth"]

        capacity = int(capacity) if capacity.isdigit() else 0

        module.capacity = Megabyte(capacity=capacity // (1024 * 1024))
        module.manufacturer = manufacturer.strip() if manufacturer else None
        module.part_number = part_number.strip() if part_number else None

        slot = MemoryModuleSlot(
            bank=bank_label.strip() if bank_label else None,
            channel=device_locator.strip() if device_locator else None,
        )
        module.slot = slot

        # The speed is already reported as MHz
        module.frequency_mhz = int(speed) if speed.isdigit() else None

        if smbios_mem_type:
            smbios_mem_type = smbios_mem_type.strip()
            module.type = MEMORY_TYPE.get(int(smbios_mem_type), "Unknown")

        if data_width and total_width:
            if int(total_width) > int(data_width):
                module.supports_ecc = True
            else:
                module.supports_ecc = False
        # Todo: Extract ECC Type
        # https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-physicalmemoryarray
        # SMBIOS Specification - Section 7.17.3 - Physical Memory Array (Type 16)

        memory_info.modules.append(module)

    return memory_info


def fetch_memory_info() -> MemoryInfo:
    return fetch_wmi_cmdlet_memory_info()
