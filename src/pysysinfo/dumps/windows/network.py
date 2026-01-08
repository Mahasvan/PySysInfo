import json
import subprocess
from typing import List

from pysysinfo.dumps.windows.interops.get_location_paths import get_location_paths
from pysysinfo.models.network_models import NICInfo, NetworkInfo
from pysysinfo.dumps.windows.common import format_acpi_path, format_pci_path
from pysysinfo.models.status_models import PartialStatus


def fetch_wmi_cmdlet_network_info() -> NetworkInfo:
    """
    Fetch NICs using WMI (PhysicalAdapter=True) and then fetch
    DEVPKEY_Device_LocationPaths for only those NICs in a batch.
    """
    command = (
        'powershell -NoProfile -Command "Get-WmiObject -Class Win32_NetworkAdapter | '
        'Where-Object { $_.PhysicalAdapter -eq $true } | '
        'Select-Object PNPDeviceID, Manufacturer, Name | '
        'ConvertTo-Csv -NoTypeInformation"'
    )

    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        return NetworkInfo(status=f"Powershell WMI cmdlet failed: {e}")

    lines = [x.split(",") for x in result.strip().splitlines()]
    lines = [[x.strip('"') for x in line] for line in lines]

    return parse_cmd_output(lines)


def parse_cmd_output(lines: List[List[str]]) -> NetworkInfo:
    header = lines[0]
    pnp_dev_idx = header.index("PNPDeviceID")
    manuf_idx = header.index("Manufacturer")
    name_idx = header.index("Name")

    network_info = NetworkInfo()
        
    for data in lines[1:]:
        module = NICInfo()
        pnp_device_id = data[pnp_dev_idx]

        if "VEN_" in pnp_device_id and "DEV_" in pnp_device_id:
            module.vendor_id = pnp_device_id.split("VEN_")[1][:4]
            module.device_id = pnp_device_id.split("DEV_")[1][:4]
        elif "VID_" in pnp_device_id and "PID_" in pnp_device_id:
            module.vendor_id = pnp_device_id.split("VID_")[1][:4]
            module.device_id = pnp_device_id.split("PID_")[1][:4]

        loc = get_location_paths(pnp_device_id)
        pci, acpi = (loc + ["", ""])[:2]

        module.pci_path = format_pci_path(pci)
        module.acpi_path = format_acpi_path(acpi)

        module.manufacturer = data[manuf_idx]
        module.controller_model = data[name_idx]
        network_info.modules.append(module)

    return network_info
