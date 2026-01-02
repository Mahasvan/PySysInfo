import subprocess
from typing import List

from pysysinfo.dumps.windows.win_enum import MEMORY_TYPE
from pysysinfo.models.memory_models import MemoryInfo, MemoryModuleInfo, MemoryModuleSlot
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import StatusType, Status

"""
the WMIC command-line utility is deprecated, and is replaced by PowerShell cmdlets.
We first check if the WMIC command works, and if it fails, we fallback to the PowerShell cmdlet.
"""


def fetch_wmic_memory_info() -> MemoryInfo:
    memory_info = MemoryInfo()
    command = ("wmic memorychip get "
               "BankLabel,Capacity,Manufacturer,PartNumber,Speed,DeviceLocator,SMBIOSMemoryType,DataWidth,TotalWidth "
               "/format:csv")
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        """
        This means the WMIC command failed - possibly because it is not available on this system.
        We mark the status as failed and return an empty MemoryInfo object, so that we can fallback to the PowerShell cmdlet.
        """
        memory_info.status.type = StatusType.FAILED
        memory_info.status.messages.append(f"WMIC command failed: {e}")
        return memory_info

    lines = result.strip().splitlines()
    lines = [line.split(",") for line in lines if line.strip()]

    return parse_cmd_output(lines)


def fetch_wmi_cmdlet_memory_info() -> MemoryInfo:
    memory_info = MemoryInfo()
    command = ('powershell -Command "Get-CimInstance Win32_PhysicalMemory | '
               'Select-Object BankLabel, Capacity, Manufacturer, PartNumber, Speed, DeviceLocator, SMBIOSMemoryType, DataWidth, TotalWidth | '
               'ConvertTo-Csv -NoTypeInformation"')
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        """
        This means the PowerShell command failed.
        This should not happen on modern Windows systems, where the wmic command is not available.
        In this case, mark status as failed and return an empty object
        """
        memory_info.status.type = StatusType.FAILED
        memory_info.status.messages.append(f"Powershell WMI cmdlet failed: {e}")
        return memory_info

    lines = [x.split(",") for x in result.strip().splitlines()]
    lines = [[x.strip('"') for x in line] for line in lines]

    return parse_cmd_output(lines)


def parse_cmd_output(lines: List[List[str]]):
    header = lines[0]
    """
    `lines` is in the following format:
    [
        ['Node', 'BankLabel', 'Capacity', 'DeviceLocator', 'Manufacturer', 'PartNumber', 'SMBIOSMemoryType', 'Speed'], <-- Header
        ['MyPCName', 'P0 CHANNEL A', '8589934592', 'DIMM 0', 'Micron Technology', 'MyPartNumber', '26', '3200'],
        ['MyPCName', 'P0 CHANNEL B', '8589934592', 'DIMM 0', 'Micron Technology', 'MyPartNumber', '26', '3200']
    ]
    
    We get the indices of the relevant columns from the header, and then parse each line accordingly.
    We cannot rely on the order we passed into the command, as that order is not followed.
    The order returned is alphabetical. If we were to add another field later, header.index() will make sure we don't break it by accident.
    """
    bank_idx = header.index("BankLabel")
    capacity_idx = header.index("Capacity")
    manufacturer_idx = header.index("Manufacturer")
    part_number_idx = header.index("PartNumber")
    speed_idx = header.index("Speed")
    device_locator_idx = header.index("DeviceLocator")
    smbios_memory_type_idx = header.index("SMBIOSMemoryType")
    data_width_idx = header.index("DataWidth")
    total_width_idx = header.index("TotalWidth")

    memory_info = MemoryInfo()
    for data in lines[1:]:
        try:
            module = MemoryModuleInfo()
            capacity = int(data[capacity_idx]) if data[capacity_idx].isdigit() else 0
            module.capacity = Megabyte(capacity=capacity // (1024 * 1024))

            if data[manufacturer_idx]:
                module.manufacturer = data[manufacturer_idx].strip()
            if data[part_number_idx]:
                module.part_number = data[part_number_idx].strip()

            slot = MemoryModuleSlot(
                bank=data[bank_idx].strip() if data[bank_idx] else None,
                channel=data[device_locator_idx].strip() if data[device_locator_idx] else None
            )
            module.slot = slot

            # The speed is already reported as MHz
            module.frequency_mhz = int(data[speed_idx]) if data[speed_idx].isdigit() else None

            if data[smbios_memory_type_idx]:
                smbios_mem_type = data[smbios_memory_type_idx].strip()
                module.type = MEMORY_TYPE.get(int(smbios_mem_type), "Unknown")

            if data[data_width_idx] and data[total_width_idx]:
                if int(data[total_width_idx]) > int(data[data_width_idx]):
                    module.supports_ecc = True
                else:
                    module.supports_ecc = False
            # Todo: Extract ECC Type
            # https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-physicalmemoryarray
            # SMBIOS Specification - Section 7.17.3 - Physical Memory Array (Type 16)

            memory_info.modules.append(module)
        except Exception as e:
            memory_info.status.type = StatusType.PARTIAL
            memory_info.status.messages.append(f"Error while parsing memory info: {e}")
    return memory_info


def fetch_memory_info() -> MemoryInfo:
    memory_info = fetch_wmic_memory_info()
    if memory_info.status.type == StatusType.FAILED:
        memory_info = fetch_wmi_cmdlet_memory_info()

    return memory_info
