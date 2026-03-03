import subprocess
from typing import List

from pysysinfo.interops.mac.bindings.gpu_info import get_gpu_info, GPUProperties
from pysysinfo.models.gpu_models import GraphicsInfo, GPUInfo, AppleExtendedGPUInfo
from pysysinfo.models.size_models import Megabyte


def check_arm():
    output = subprocess.run(['uname', '-m'], capture_output=True).stdout.decode("utf-8")
    if "arm" in output.lower():
        return True
    return False

def fetch_graphics_info():
    gpu_info: List[GPUProperties] = get_gpu_info()
    graphics_info = GraphicsInfo()
    graphics_info.modules = []
    for gpu in gpu_info:
        module = GPUInfo()
        module.name = gpu.name

        if not module.name:
            graphics_info.status.make_partial("Could not get GPU Name")

        module.vendor_id = hex(gpu.vendor_id)
        if module.vendor_id:
            if hex(gpu.vendor_id).lower() == "0x106b": module.manufacturer = "Apple Inc."
            elif hex(gpu.vendor_id).lower() == "0x10de": module.manufacturer = "Nvidia"
            elif hex(gpu.vendor_id).lower() == "0x1002": module.manufacturer = "AMD"
            elif hex(gpu.vendor_id).lower() == "0x8086": module.manufacturer = "Intel"
            else: module.manufacturer = "Unknown"
        else:
            graphics_info.status.make_partial("Could not get GPU vendor ID")

        if not gpu.device_id:
            if not gpu.is_apple_silicon:
                graphics_info.status.make_partial(f"Could not get Device ID for {module.name}")
        else:
            module.device_id = hex(gpu.device_id)

        if gpu.is_apple_silicon:
            module.vram = Megabyte(capacity=gpu.apple_gpu.unified_memory_mb)

            module.apple_gpu_info = AppleExtendedGPUInfo()
            module.apple_gpu_info.gpu_core_count = gpu.apple_gpu.core_count
            module.apple_gpu_info.performance_shader_count = gpu.apple_gpu.gpu_perf_shaders
            module.apple_gpu_info.gpu_gen = gpu.apple_gpu.gpu_gen


        graphics_info.modules.append(module)
    return graphics_info


"""
This older fetch_graphics_info uses pyobjc to connect to IOKit. 
This has been replaced by means of C++ bindings to the dylib. 
Refer `src/interops/mac`. 

def old_fetch_graphics_info() -> GraphicsInfo:
    
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
"""
