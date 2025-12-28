import subprocess

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

    lines = result.strip().splitlines()
    lines = [line.split(",") for line in lines if line.strip()]

    return parse_cmd_output(lines)


def fetch_wmi_cmdlet_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    command = ('powershell -Command "Get-CimInstance Win32_VideoController | '
               'Select-Object "AdapterCompatibility,Name,AdapterRAM,VideoProcessor,PCPDeviceID" | '
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

    lines = [x.split(",") for x in result.strip().splitlines()]
    lines = [[x.strip('"') for x in line] for line in lines]

    return parse_cmd_output(lines)

def parse_cmd_output(lines: list) -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    print(lines)
    return graphics_info



def fetch_graphics_info() -> GraphicsInfo:
    graphics_info = fetch_wmic_graphics_info()
    if type(graphics_info.status) is FailedStatus:
        graphics_info = fetch_wmi_cmdlet_graphics_info()
    return graphics_info