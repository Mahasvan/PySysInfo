import binascii
import subprocess

from pysysinfo.dumps.mac.common import construct_pci_path_mac
from pysysinfo.dumps.mac.ioreg import *
from pysysinfo.models.gpu_models import GraphicsInfo, GPUInfo
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import StatusType


def check_arm():
    output = subprocess.run(['uname', '-m'], capture_output=True).stdout.decode("utf-8")
    if "arm" in output.lower():
        return True
    return False


def fetch_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()
    is_arm = check_arm()

    if not is_arm:
        # x86 machines enumerate their GPUs differently
        device = {
            "IOProviderClass": "IOPCIDevice",
            # Bit mask matching, ensuring that the 3rd byte is one of the display controller (0x03).
            "IOPCIClassMatch": "0x03000000&0xff000000",
        }
    else:
        device = {"IONameMatched": "gpu*"}

    interface = ioiterator_to_list(
        IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
    )

    if not interface:
        graphics_info.status.type = StatusType.FAILED
        graphics_info.status.messages.append("Could not enumerate GPUs")
        return graphics_info

    for i in interface:
        device = corefoundation_to_native(
            IORegistryEntryCreateCFProperties(
                i, None, kCFAllocatorDefault, kNilOptions
            )
        )[1]

        try:
            # For Apple's M1 iGFX
            if (
                    is_arm
                    and
                    # If both return true, that means
                    # we aren't dealing with a GPU device.
                    not "gpu" in device.get("IONameMatched", "").lower()
                    and not "AGX" in device.get("CFBundleIdentifierKernel", "")
            ):
                continue
        except:
            continue

        model = device.get("model", None)
        if not model:
            continue

        gpu = GPUInfo()
        gpu.name = model

        try:
            gpu.vendor_id = "0x" + (
                binascii.b2a_hex(bytes(reversed(device.get("vendor-id")))).decode()[
                    4:
                ]
            )

            if not is_arm:
                gpu.device_id = "0x" + (
                    binascii.b2a_hex(
                        bytes(reversed(device.get("device-id")))
                    ).decode()[4:]
                )
                # todo: get VRAM for non-ARM devices
            else:
                gpu_config = device.get("GPUConfigurationVariable", {})
                gpu.apple_gpu_core_count = gpu_config.get("num_cores")
                gpu.apple_neural_core_count = gpu_config.get("num_gps")
                gpu.manufacturer = "Apple Inc."
                gpu.subsystem_manufacturer = "Apple Inc."
                # We use subsystem_model for the gpu generation
                gpu.subsystem_model = str(gpu_config.get("gpu_gen")) if gpu_config.get("gpu_gen") else None

                memory = subprocess.run(["sysctl", "hw.memsize"], capture_output=True).stdout.decode("utf-8")
                memory = memory.split(":")[1].strip()
                if memory.isnumeric():
                    gpu.vram = Megabyte(capacity=int(memory) // (1024 ** 2))

            # Now we get the ACPI path for x86 devices
            if not is_arm:
                data = construct_pci_path_mac(
                    i, device.get("acpi-path", "")
                )
                gpu.pci_path = data.get("pci_path")
                gpu.acpi_path = data.get("acpi_path")

            graphics_info.modules.append(gpu)

        except Exception as e:
            graphics_info.status.type = StatusType.PARTIAL
            graphics_info.status.messages.append(f"Failed to enumerate GPU: {e}")

    return graphics_info
