import ctypes
import re
import time
import winreg
from typing import Optional

from pysysinfo.dumps.windows.common import format_acpi_path, format_pci_path
from pysysinfo.interops.win.api.signatures import GetWmiInfo
from pysysinfo.models.gpu_models import GPUInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import StatusType
from pysysinfo.util.location_paths import fetch_device_properties, fetch_pcie_info


def fetch_additional_properties(
        pnp_device_id: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Fetch additional device properties using Windows Configuration Manager API.

    Args:
        pnp_device_id: The PNP Device ID string

    Returns:
        Tuple of (acpi_path, pci_root, bus_number, device_address)
    """
    location_paths, bus_number, device_address = fetch_device_properties(pnp_device_id)

    if not location_paths:
        return None, None, bus_number, device_address

    acpi_path = None
    pci_root = None

    for path in location_paths:
        if path.startswith("ACPI"):
            acpi_path = path
        if path.startswith("PCIROOT"):
            pci_root = path

    return acpi_path, pci_root, bus_number, device_address


def fetch_vram_from_registry(device_name: str, driver_version: str) -> Optional[int]:
    key_path = (
        r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    )
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
                        vram_bytes, _ = winreg.QueryValueEx(
                            subkey, "HardwareInformation.qwMemorySize"
                        )
                        if vram_bytes:
                            return int(vram_bytes)
                        alt_vram_bytes, _ = winreg.QueryValueEx(
                            subkey, "HardwareInformation.MemorySize"
                        )
                        if alt_vram_bytes:
                            return int(alt_vram_bytes)
            except:
                continue

    return None


def fetch_fast_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()

    # 256 bytes per property, 6 properties, 2 modules
    buf_size = 256 * 6 * 2
    buffer = ctypes.create_string_buffer(buf_size)

    GetWmiInfo(
        b"SELECT AdapterCompatibility,Name,AdapterRAM,VideoProcessor,PNPDeviceID,DriverVersion FROM Win32_VideoController",
        b"ROOT\\CIMV2",
        buffer,
        buf_size,
    )

    raw_data = buffer.value.decode("utf-8", errors="ignore")

    if not raw_data:
        graphics_info.status.type = StatusType.FAILED
        graphics_info.status.messages.append("WMI query returned no data")
        return graphics_info

    for line in raw_data.split("\n"):
        if not line or "|" not in line:
            continue

        gpu = GPUInfo()
        unparsed = line.split("|")

        parsed_data = {
            x.split("=", 1)[0]: x.split("=", 1)[1] for x in unparsed if "=" in x
        }

        ven_dev_subsys_regex = re.compile(
            r"VEN_([0-9a-fA-F]{4}).*DEV_([0-9a-fA-F]{4}).*SUBSYS_([0-9a-fA-F]{4})([0-9a-fA-F]{4})"
        )

        gpu.name = parsed_data["Name"]
        gpu.manufacturer = parsed_data["AdapterCompatibility"]
        pnp_device_id = parsed_data["PNPDeviceID"]
        drv_version = parsed_data["DriverVersion"]

        if "PCI" not in pnp_device_id.upper():
            continue  # Skip non-PCI GPUs (virtual adapters, etc.)

        start = time.time()
        acpi_path, pci_root, bus_number, device_address = fetch_additional_properties(
            pnp_device_id
        )
        print("Time for additional details:", time.time() - start)
        gpu.acpi_path = format_acpi_path(acpi_path)
        gpu.pci_path = format_pci_path(pci_root)

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
        vram = parsed_data["AdapterRAM"]

        if vram and (int(vram) >= 4_194_304_000 or int(vram) <= 0):
            # WMI's VRAM entry is a signed 32-bit integer. The maximum value it can show is 4095MB.
            # If it is more than 4000 MB, we query the registry instead, for accuracy
            vram_bytes = fetch_vram_from_registry(gpu.name, drv_version)
            gpu.vram = Megabyte(capacity=(vram_bytes // 1024 // 1024))
        elif vram:
            gpu.vram = Megabyte(capacity=(int(vram) // 1024 // 1024))

        pcie_info = fetch_pcie_info(pnp_device_id)

        if pcie_info:
            gpu.pcie_gen, gpu.pcie_width = pcie_info

        # !!! Leaving this here just in case we need to revert !!!

        # Attempt to get PCIe width and link speed for Nvidia
        # if gpu.vendor_id and gpu.vendor_id.lower() == "0x10de":
        #     # device_address is a 32 bit integer, where the high 16 bits are Device number
        #     # and the low 16 bits are the function number.
        #     # The format of the PCI location string is {domain}:{bus}:{device}.{function}
        #     # We can assume domain is 0000
        #     # todo: requires testing
        #     device_num = (int(device_address) >> 16) & 0xFFFF
        #     func_num = int(device_address) & 0xFFFF
        #     nvidia_smi_id = (
        #         f"0000:{int(bus_number):02x}:{device_num:02x}.{func_num:02x}"
        #     )
        #     gpu_name, pci_width, pci_gen, vram_total = fetch_gpu_details_nvidia(
        #         nvidia_smi_id
        #     )
        #     if pci_width:
        #         gpu.pcie_width = pci_width
        #     if pci_gen:
        #         gpu.pcie_gen = pci_gen
        # todo: From what I looked, there is no consistent reliable method to get this additional info for AMD GPUs.
        # todo: Additional details for Intel ARC GPUs

        graphics_info.modules.append(gpu)

    return graphics_info


def fetch_graphics_info() -> GraphicsInfo:
    return fetch_fast_graphics_info()
