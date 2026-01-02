import glob
import os
import subprocess
from typing import Optional

from pysysinfo.dumps.linux.common import get_pci_path_linux
from pysysinfo.models.gpu_models import GPUInfo, GraphicsInfo
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import StatusType
from pysysinfo.util.nvidia import fetch_gpu_details_nvidia


# Currently, the info in /sys/class/drm/cardX is being used.
# todo: Check if lspci and lshw -c display can be used
# https://unix.stackexchange.com/questions/393/how-to-check-how-many-lanes-are-used-by-the-pcie-card

def fetch_vram_amd(device) -> Optional[int]:
    ROOT_PATH = "/sys/bus/pci/devices/"
    vram_files = os.path.join(*[ROOT_PATH, device, "drm", "card*", "device", "mem_info_vram_total"])
    try:
        drm_files = glob.glob(vram_files)
        if drm_files:
            with open(drm_files[0]) as f:
                vram_bits = int(f.read().strip())
                vram_mb = int(vram_bits / 1024 / 1024)
                return vram_mb
        return None
    except:
        return None


def get_pcie_gen(device) -> Optional[int]:
    # Path example: /sys/bus/pci/devices/0000:03:00.0/current_link_speed
    path = f"/sys/bus/pci/devices/{device}/current_link_speed"

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            raw_speed = f.read().strip()  # e.g., "16.0 GT/s"

        # Mapping Dictionary
        speed_to_gen = {
            "2.5 GT/s": 1,
            "5.0 GT/s": 2,
            "8.0 GT/s": 3,
            "16.0 GT/s": 4,
            "32.0 GT/s": 5,
            "64.0 GT/s": 6
        }

        for k, v in speed_to_gen.items():
            """ `8.0 GT/s PCIe` may be a possible candidate"""
            if k in raw_speed:
                return v

        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def fetch_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()

    ROOT_PATH = "/sys/bus/pci/devices/"

    if not os.path.exists(ROOT_PATH):
        graphics_info.status.type = StatusType.FAILED
        graphics_info.status.messages.append("/sys/bus/pci/devices/ not found")
        return graphics_info

    for device in os.listdir(ROOT_PATH):
        # print("Found device: ", device)
        try:
            path = os.path.join(ROOT_PATH, device)
            device_class = open(os.path.join(path, "class")).read().strip()
            """
            The class code is three hex-bytes, where the leftmost hex-byte is the base class
            We want the devices of base class 0x03, which denotes a Display Controller.
            """
            class_code = int(device_class, base=16)

            base_class = class_code >> 16
            if base_class != 3:
                continue
        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not open file for {device}: {e}")
            continue

        gpu = GPUInfo()

        try:
            gpu.vendor_id = open(os.path.join(path, "vendor")).read().strip()
            gpu.device_id = open(os.path.join(path, "device")).read().strip()
            width = open(os.path.join(path, "current_link_width")).read().strip()
            if width.isnumeric() and int(width) > 0:
                gpu.pcie_width = int(width)
        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not get GPU properties: {e}")
        try:
            acpi_path = open(os.path.join(path, "firmware_node", "path")).read().strip()
            gpu.acpi_path = acpi_path
        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not get ACPI path: {e}")
        try:
            pci_path = get_pci_path_linux(device)
            gpu.pci_path = pci_path
        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not get PCI path: {e}")

        try:
            pcie_gen = get_pcie_gen(device)
            if pcie_gen:
                gpu.pcie_gen = pcie_gen
        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not get PCI gen: {e}")

        if gpu.vendor_id == "0x1002":
            # get VRAM for AMD GPUs
            vram_capacity = fetch_vram_amd(device)
            if vram_capacity is not None:
                gpu.vram = Megabyte(capacity=vram_capacity)

        elif gpu.vendor_id and gpu.vendor_id.lower() == "0x10de":
            # get VRAM for Nvidia GPUs
            try:
                gpu_name, pcie_width, pcie_gen, vram_total = fetch_gpu_details_nvidia(device)
                if gpu_name: gpu.name = gpu_name
                if pcie_width: gpu.pcie_width = pcie_width
                if pcie_gen: gpu.pcie_gen = pcie_gen
                if vram_total: gpu.vram = Megabyte(capacity=vram_total)
            except Exception as e:
                graphics_info.status.type = StatusType.PARTIAL
                graphics_info.status.messages.append(f"Could not get additional GPU info for NVIDIA GPU {device}: {e}")
        try:
            lspci_output = subprocess.run(["lspci", "-s", device, "-vmm"], capture_output=True, text=True).stdout
            # We gather all data here and parse whatever data we have. Subsystem data may not be returned.
        except Exception as e:
            # lspci may not be available in some distros
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not get lspci output for {device}: {e}")
            graphics_info.modules.append(gpu)
            continue

        try:
            data = {}
            for line in lspci_output.splitlines():
                if ":" in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()

            gpu.manufacturer = data.get("Vendor")
            gpu.name = data.get("Device")
            gpu.subsystem_manufacturer = data.get("SVendor")
            gpu.subsystem_model = data.get("SDevice")
        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Could not parse LSPCI output for GPU {device}: {e}")

        graphics_info.modules.append(gpu)

    return graphics_info
