import csv
import html
import io
import json
import re
import subprocess
import winreg
from typing import Optional

from src.pysysinfo.dumps.windows.common import format_acpi_path, format_pci_path
from src.pysysinfo.models.gpu_models import GPUInfo
from src.pysysinfo.models.gpu_models import GraphicsInfo
from src.pysysinfo.models.size_models import Megabyte
from src.pysysinfo.models.status_models import FailedStatus
from src.pysysinfo.models.status_models import PartialStatus


def fetch_acpi_path(pnp_device_id: str):
    escaped = html.unescape(pnp_device_id)
    ps_script = f"""
        Get-PnpDeviceProperty -InstanceId "{escaped}" -KeyName DEVPKEY_Device_LocationPaths | 
        Select-Object -ExpandProperty Data | ConvertTo-Json
        """
    pass
    try:
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    except:
        return None
    if not result.stdout and not result.stdout.strip():
        return None

    paths = json.loads(result.stdout)
    acpi_path = None
    pciroot = None

    for path in paths:
        if path.startswith("ACPI"):
            acpi_path = path
        if path.startswith("PCIROOT"):
            pciroot = path

    return acpi_path, pciroot


def fetch_vram_from_registry(device_name: str, driver_version: str) -> Optional[int]:
    key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
        # Iterate subkeys (0000, 0001, etc) to find the one matching our PNPDeviceID
        for i in range(100):
            try:
                sub_key_name = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, sub_key_name) as subkey:
                    # Check if this registry entry belongs to our device
                    # Often stored in "MatchingDeviceId" or similar,
                    # but robust matching requires correlating "DriverDesc" or "InfSection"

                    # FAST METHOD: Try to read qwMemorySize directly if Name matches
                    drv_desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                    drv_version, _ = winreg.QueryValueEx(subkey, "DriverVersion")

                    if drv_desc == device_name and drv_version == driver_version:
                        vram_bytes, _ = winreg.QueryValueEx(subkey, "HardwareInformation.qwMemorySize")
                        if vram_bytes:
                            return int(vram_bytes)
                        alt_vram_bytes, _ = winreg.QueryValueEx(subkey, "HardwareInformation.MemorySize")
                        if alt_vram_bytes:
                            return int(alt_vram_bytes)
            except:
                continue

    return None


def fetch_wmic_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    command = ("wmic path Win32_VideoController get "
               "AdapterCompatibility,Name,AdapterRAM,VideoProcessor,PNPDeviceID,DriverVersion "
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
    if len(set([len(x) for x in lines])) != 1:
        # If we have errors parsing the csv, we will have uneven lengths across rows.
        graphics_info.status = FailedStatus("Error parsing output, abnormal CSV structure")
        return graphics_info
    return parse_cmd_output(lines)


def fetch_wmi_cmdlet_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    command = ('powershell -Command "Get-CimInstance Win32_VideoController | '
               'Select-Object "AdapterCompatibility,Name,AdapterRAM,VideoProcessor,PNPDeviceID,DriverVersion" | '
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
    vram_idx = headers.index("AdapterRAM")
    drv_version_idx = headers.index("DriverVersion")

    ven_dev_subsys_regex = re.compile(
        r"VEN_([0-9a-fA-F]{4}).*DEV_([0-9a-fA-F]{4}).*SUBSYS_([0-9a-fA-F]{4})([0-9a-fA-F]{4})")

    for line in lines[1:]:
        try:
            gpu = GPUInfo()
            gpu.model = line[name_idx]
            gpu.manufacturer = line[manufacturer_idx]
            pnp_device_id = line[pnp_device_idx]
            drv_version = line[drv_version_idx]

            acpi_path, pci_path = fetch_acpi_path(pnp_device_id)
            gpu.acpi_path = format_acpi_path(acpi_path)
            gpu.pci_path = format_pci_path(pci_path)

            """
            The PNPDeviceID is of the form ****VEN_1234&DEV_5678&SUBSYS_9ABCDE0F.****
            we use the regular expression defined above to get the Vendor and device ids as VEN_{ABCD}&DEV_{PQRS}
            where ABCD and PQRS are 4 hex digits. 
            Same goes for subsystem vendor and device ID. 
            One thing to note is that WMI does not expose the strings for subsystem vendor name and model name, like Linux. 
            So we return the values as they are, prefixed with "0x" for clarity. 
            todo: PCI lookup? 
            """
            match = ven_dev_subsys_regex.findall(pnp_device_id)
            if match:
                vendor_id, device_id, subsystem_model_id, subsystem_manuf_id = match[0]
                gpu.vendor_id = f"0x{vendor_id}"
                gpu.device_id = f"0x{device_id}"
                gpu.subsystem_model = f"0x{subsystem_model_id}"
                gpu.subsystem_manufacturer = f"0x{subsystem_manuf_id}"

            # Attempt to get VRAM details
            vram = line[vram_idx]

            if vram and int(vram) >= 4_194_304_000:
                # WMI's VRAM entry is a signed 32-bit integer. The maximum value it can show is 4095MB.
                # If it is more than 4000 MB, we query the registry instead, for accuracy
                vram_bytes = fetch_vram_from_registry(gpu.model, drv_version)
                gpu.vram = Megabyte(capacity=(vram_bytes // 1024 // 1024))
            elif vram:
                gpu.vram = Megabyte(capacity=(int(vram) // 1024 // 1024))

            graphics_info.modules.append(gpu)

        except Exception as e:
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
            graphics_info.status.messages.append(f"Error parsing GPU info: {e}")
    return graphics_info


def fetch_graphics_info() -> GraphicsInfo:
    graphics_info = fetch_wmic_graphics_info()
    if type(graphics_info.status) is FailedStatus:
        graphics_info = fetch_wmi_cmdlet_graphics_info()
    return graphics_info
