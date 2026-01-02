import subprocess
from typing import List

from pysysinfo.dumps.windows.win_enum import MEDIA_TYPE, BUS_TYPE
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import PartialStatus, FailedStatus
from pysysinfo.models.storage_models import StorageInfo, DiskInfo


def fetch_wmic_storage_info() -> StorageInfo:
    storage_info = StorageInfo()

    command = r"wmic /namespace:\\root\Microsoft\Windows\Storage path MSFT_PhysicalDisk get FriendlyName,MediaType,BusType,Size,Manufacturer /format:csv"
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        """
        This means the WMIC command failed - possibly because it is not available on this system.
        We mark the status as failed and return an empty StorageInfo object, so that we can fallback to the PowerShell cmdlet.
        """
        storage_info.status = FailedStatus(f"WMIC Command failed: {e}")
        return storage_info

    lines = result.strip().splitlines()
    lines = [line.split(",") for line in lines if line.strip()]

    return parse_cmd_output(lines)


def fetch_wmi_cmdlet_storage_info() -> StorageInfo:
    storage_info = StorageInfo()

    command = r'powershell -Command "Get-CimInstance -Namespace "root/Microsoft/Windows/Storage" -ClassName MSFT_PhysicalDisk | Select-Object FriendlyName, MediaType, BusType, Size, Manufacturer | ConvertTo-Csv -NoTypeInformation"'
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        """
        This means the PowerShell command failed.
        This should not happen on modern Windows systems, where the wmic command is not available.
        In this case, mark status as failed and return an empty object
        """
        storage_info.status = FailedStatus(f"WMI Powershell cmdlet failed: {e}")
        return storage_info

    lines = [x.split(",") for x in result.strip().splitlines()]
    lines = [[x.strip('"') for x in line] for line in lines]

    return parse_cmd_output(lines)


def parse_cmd_output(lines: List[List[str]]) -> StorageInfo:
    header = lines[0]

    size_idx = header.index("Size")
    media_type_idx = header.index("MediaType")
    bus_type_idx = header.index("BusType")
    friendly_name_idx = header.index("FriendlyName")
    manufacturer_idx = header.index("Manufacturer")

    storage_info = StorageInfo()

    for line in lines[1:]:
        try:
            # print("Size:", line[size_idx])
            # print("Media Type:", line[media_type_idx])
            # print("Bus Type:", line[bus_type_idx])
            # print("Friendly Name:", line[friendly_name_idx])
            disk = DiskInfo()

            disk.model = line[friendly_name_idx]
            disk.manufacturer = line[manufacturer_idx].strip() if line[manufacturer_idx].strip() else None
            disk.type = MEDIA_TYPE.get(int(line[media_type_idx]), "Unknown")
            disk.size = Megabyte(capacity=int(line[size_idx]) // (1024 * 1024)) if line[size_idx].isdigit() else None

            conn_type, location = None, None
            bus_type = BUS_TYPE.get(int(line[bus_type_idx]), None)
            if bus_type:
                conn_type = bus_type["type"]
                location = bus_type["location"]

            disk.connector = conn_type
            disk.location = location

            if conn_type and "nvme" in conn_type.lower():
                disk.type = MEDIA_TYPE[4]  # Solid State Drive (SSD)

            storage_info.modules.append(disk)

        except Exception as e:
            storage_info.status = PartialStatus(messages=storage_info.status.messages)
            storage_info.status.messages.append(f"Error processing disk info: {e}")
    return storage_info


def fetch_storage_info() -> StorageInfo:
    """
    First tries to fetch storage info using the WMIC command.
    If that fails, falls back to using the PowerShell cmdlet.
    """
    response = fetch_wmic_storage_info()
    if isinstance(response.status, FailedStatus):
        response = fetch_wmi_cmdlet_storage_info()

    return response
