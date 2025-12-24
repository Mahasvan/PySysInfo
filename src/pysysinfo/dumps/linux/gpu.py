import os

from src.pysysinfo.dumps.linux.common import pci_from_acpi_linux
from src.pysysinfo.models.gpu_models import GPUInfo, GraphicsInfo
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus

# Currently, the info in /sys/class/drm/cardX is being used.
# todo: Check if lspci and lshw -c display can be used
# https://unix.stackexchange.com/questions/393/how-to-check-how-many-lanes-are-used-by-the-pcie-card

def fetch_gpu_info() -> GraphicsInfo:
    gpu_info = GraphicsInfo()

    if not os.path.exists("/sys/class/drm"):
        gpu_info.status = FailedStatus("/sys/class/drm does not exist")
        # WSL for example does not have this.
        return gpu_info

    for file in os.listdir("/sys/class/drm/"):
        # DRM devices (not FBDev) are enumerated with the format `cardX`
        # inside of sysfs's DRM directory. So we look for those, and traverse
        # them. We look for the `device` and `vendor` file, which should always be there.
        if ("card" in file) and ("-" not in file):
            gpu = GPUInfo()
            try:
                path = f"/sys/class/drm/{file}/device"
                ven = open(f"{path}/vendor", "r").read().strip()
                dev = open(f"{path}/device", "r").read().strip()
                gpu.vendor_id = ven
                gpu.device_id = dev

                acpi_path, pci_path = pci_from_acpi_linux(path)
                if acpi_path:
                    gpu.acpi_path = acpi_path
                if pci_path:
                    gpu.pci_path = pci_path

                gpu_info.modules.append(gpu)

            except Exception as e:
                gpu_info.status = PartialStatus(messages=gpu_info.status.messages)
                gpu_info.status.messages.append(f"Failed to get detail for {file}: {e}")
                continue

    return gpu_info

