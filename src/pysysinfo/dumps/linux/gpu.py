import os
import subprocess

from src.pysysinfo.dumps.linux.common import get_pci_path_linux
from src.pysysinfo.models.gpu_models import GPUInfo, GraphicsInfo
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus

# Currently, the info in /sys/class/drm/cardX is being used.
# todo: Check if lspci and lshw -c display can be used
# https://unix.stackexchange.com/questions/393/how-to-check-how-many-lanes-are-used-by-the-pcie-card

def fetch_gpu_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()

    ROOT_PATH = "/sys/bus/pci/devices/"

    if not os.path.exists(ROOT_PATH):
        graphics_info.status = FailedStatus("/sys/bus/pci/devices/ not found")
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
            graphics_info.status = FailedStatus(f"Could not open file for {device}: {e}")
            return graphics_info

        gpu = GPUInfo()

        try:
            gpu.vendor_id = open(os.path.join(path, "vendor")).read().strip()
            gpu.device_id = open(os.path.join(path, "device")).read().strip()
            width = open(os.path.join(path, "current_link_width")).read().strip()
            if width.isnumeric() and int(width) > 0:
                gpu.width = int(width)
        except Exception as e:
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
            graphics_info.status.messages.append(f"Could not get GPU properties: {e}")
        try:
            acpi_path = open(os.path.join(path, "firmware_node", "path")).read().strip()
            gpu.acpi_path = acpi_path
        except Exception as e:
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
            graphics_info.status.messages.append(f"Could not get ACPI path: {e}")
        try:
            pci_path = get_pci_path_linux(device)
            gpu.pci_path = pci_path
        except Exception as e:
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
            graphics_info.status.messages.append(f"Could not get PCI path: {e}")

        try:
            lspci_output = subprocess.run(["lspci", "-s", device, "-vmm"], capture_output=True, text=True).stdout
            # We gather all data here and parse whatever data we have. Subsystem data may not be returned.
        except Exception as e:
            # lspci may not be available in some distros
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
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
            gpu.model = data.get("Model")
            gpu.subsystem_manufacturer = data.get("SVendor")
            gpu.subsystem_model = data.get("SDevice")
        except Exception as e:
            graphics_info.status = PartialStatus(messages=graphics_info.status.messages)
            graphics_info.status.messages.append(f"Could not parse LSPCI output for GPU {device}: {e}")

        graphics_info.modules.append(gpu)

    return graphics_info