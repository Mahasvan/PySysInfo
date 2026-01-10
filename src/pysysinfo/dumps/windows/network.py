import ctypes
import json
import subprocess
from typing import List

from pysysinfo.interops.win.api.signatures import GetWmiInfo
from pysysinfo.util.location_paths import get_location_paths
from pysysinfo.models.network_models import NICInfo, NetworkInfo
from pysysinfo.dumps.windows.common import format_acpi_path, format_pci_path
from pysysinfo.models.status_models import Status, StatusType


def fetch_wmi_cmdlet_network_info() -> NetworkInfo:
    network_info = NetworkInfo(status=Status(type=StatusType.SUCCESS))

    raw_data = ctypes.create_string_buffer(1024 * 10)
    GetWmiInfo(
        b"SELECT PNPDeviceID, Manufacturer, Name FROM Win32_NetworkAdapter WHERE PhysicalAdapter=True",
        b"ROOT\\CIMV2",
        raw_data,
        1024 * 10,
    )

    try:
        decoded = raw_data.value.decode("utf-8")
    except Exception:
        network_info.status.type = StatusType.FAILED
        network_info.status.messages.append("Failed to decode WMI output")
        return network_info

    for data in decoded.split("\n"):
        if not data or "|" not in data:
            continue

        module = NICInfo()
        parsed = {
            x.split("=", 1)[0]: x.split("=", 1)[1] for x in data.split("|") if "=" in x
        }

        pnp_device_id = parsed.get("PNPDeviceID", None)
        manufacturer = parsed.get("Manufacturer", None)
        name = parsed.get("Name", None)

        if "VEN_" in pnp_device_id and "DEV_" in pnp_device_id:
            module.vendor_id = pnp_device_id.split("VEN_")[1][:4]
            module.device_id = pnp_device_id.split("DEV_")[1][:4]
        elif "VID_" in pnp_device_id and "PID_" in pnp_device_id:
            module.vendor_id = pnp_device_id.split("VID_")[1][:4]
            module.device_id = pnp_device_id.split("PID_")[1][:4]

        loc = get_location_paths(pnp_device_id)

        if loc is not None:
            pci, acpi = (loc + ["", ""])[:2]

            module.pci_path = format_pci_path(pci)
            module.acpi_path = format_acpi_path(acpi)
        else:
            network_info.status.type = StatusType.PARTIAL
            network_info.status.messages.append(
                f"Could not determine location paths for NIC with PNPDeviceID: {pnp_device_id}"
            )

        module.manufacturer = manufacturer
        module.name = name
        network_info.modules.append(module)

    return network_info
