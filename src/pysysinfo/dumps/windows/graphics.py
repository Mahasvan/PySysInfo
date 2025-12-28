import csv
import io
import subprocess
import re

from pysysinfo.models.gpu_models import GPUInfo
from pysysinfo.models.status_models import PartialStatus
from src.pysysinfo.models.gpu_models import GraphicsInfo
from src.pysysinfo.models.memory_models import MemoryInfo
from src.pysysinfo.models.status_models import FailedStatus


def fetch_wmic_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    command = ("wmic path Win32_VideoController get "
               "AdapterCompatibility,Name,AdapterRAM,VideoProcessor,PNPDeviceID "
               "/format:csv")
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        """
        This means the WMIC command failed - possibly because it is not available on this system.
        We mark the status as failed and return an empty MemoryInfo object, so that we can fallback to the PowerShell cmdlet.
        """
        graphics_info.status = FailedStatus(f"WMIC command failed: {e}")
        return graphics_info

    result = result.replace(", Inc", " Inc")
    # Hacky fix that solves CSV splitting errors when "Advanced Micro Devices, Inc." is split between the comma.
    # So we rely on the better parsing using cmdlet, and this as the backup
    lines = result.strip().splitlines()
    lines = [line.split(",") for line in lines if line.strip()]

    return parse_cmd_output(lines)


def fetch_wmi_cmdlet_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    command = ('powershell -Command "Get-CimInstance Win32_VideoController | '
               'Select-Object "AdapterCompatibility,Name,AdapterRAM,VideoProcessor,PNPDeviceID" | '
               'ConvertTo-Csv -NoTypeInformation"')
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        """
        This means the PowerShell command failed.
        This should not happen on modern Windows systems, where the wmic command is not available.
        In this case, mark status as failed and return an empty object
        """
        graphics_info.status = FailedStatus(f"Powershell WMI cmdlet failed: {e}")
        return graphics_info

    rows = csv.reader(io.StringIO(result))

    return parse_cmd_output(list(rows))

def parse_cmd_output(lines: list) -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    if len(lines) < 2:
        graphics_info.status = FailedStatus("No data returned from WMI")
        return graphics_info
    headers = lines[0]
    name_idx = headers.index("Name")
    manufacturer_idx = headers.index("AdapterCompatibility")
    pnp_device_idx = headers.index("PNPDeviceID")

    ven_dev_subsys_regex = re.compile(r"VEN_([0-9a-fA-F]{4}).*DEV_([0-9a-fA-F]{4}).*SUBSYS_([0-9a-fA-F]{4})([0-9a-fA-F]{4})")
    for line in lines[1:]:
        try:
            gpu = GPUInfo()
            gpu.model = line[name_idx]
            gpu.manufacturer = line[manufacturer_idx]
            pnp_device_id = line[pnp_device_idx]
            match = ven_dev_subsys_regex.findall(pnp_device_id)
            if match:
                vendor_id, device_id, subsystem_model_id, subsystem_manuf_id = match[0]
                gpu.vendor_id = f"0x{vendor_id}"
                gpu.device_id = f"0x{device_id}"
                gpu.subsystem_model = f"0x{subsystem_model_id}"
                gpu.subsystem_manufacturer = f"0x{subsystem_manuf_id}"

            graphics_info.modules.append(gpu)
        except Exception as e:
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
            graphics_info.status.messages.append(f"Error parsing GPU info: {e}")
    return graphics_info



def fetch_graphics_info() -> GraphicsInfo:
    graphics_info = fetch_wmi_cmdlet_graphics_info()
    if type(graphics_info.status) is FailedStatus:
        graphics_info = fetch_wmic_graphics_info()
    return graphics_info