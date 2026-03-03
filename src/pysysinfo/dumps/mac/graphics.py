from typing import List

from pysysinfo.models.gpu_models import GraphicsInfo, GPUInfo, AppleExtendedGPUInfo
from pysysinfo.models.size_models import Megabyte
from pysysinfo.models.status_models import StatusType

_VENDOR_MAP = {
    0x106B: "Apple Inc.",
    0x10DE: "Nvidia",
    0x1002: "AMD",
    0x8086: "Intel",
}


def fetch_graphics_info() -> GraphicsInfo:
    graphics_info = GraphicsInfo()

    # The binding raises FileNotFoundError at import time if libdevice_info.dylib is missing,
    # and RuntimeError at call time if the C library returns -1
    try:
        from pysysinfo.interops.mac.bindings.gpu_info import get_gpu_info, GPUProperties
        gpu_list: List[GPUProperties] = get_gpu_info()

    except FileNotFoundError as e:
        graphics_info.status.type = StatusType.FAILED
        graphics_info.status.messages.append(f"libdevice_info.dylib not found – rebuild the CMake project: {e}")
        return graphics_info

    except RuntimeError as e:
        # get_gpu_info() returns -1 when IOKit enumeration fails
        graphics_info.status.type = StatusType.FAILED
        graphics_info.status.messages.append(f"IOKit GPU enumeration failed: {e}")
        return graphics_info

    except Exception as e:
        graphics_info.status.type = StatusType.FAILED
        graphics_info.status.messages.append(f"Unexpected error loading GPU binding: {e}")
        return graphics_info

    for gpu in gpu_list:
        module = GPUInfo()

        module.name = gpu.name if gpu.name else None
        if not module.name:
            graphics_info.status.make_partial("Could not get GPU name")

        if gpu.vendor_id:
            module.vendor_id = hex(gpu.vendor_id)
            module.manufacturer = _VENDOR_MAP.get(gpu.vendor_id, "Unknown")
        else:
            graphics_info.status.make_partial(
                f"Could not get vendor ID for GPU: {module.name}"
            )

        # Apple Silicon GPUs report 0x0000 for device_id. Flag it as partial for non-Apple-Silicon GPUs.
        if gpu.device_id:
            module.device_id = hex(gpu.device_id)
        elif not gpu.is_apple_silicon:
            graphics_info.status.make_partial(f"Could not get device ID for GPU: {module.name}")

        # Apple Silicon extended info
        if gpu.is_apple_silicon:
            if gpu.apple_gpu is None:
                graphics_info.status.make_partial(
                    f"Apple Silicon GPU detected but extended properties are unavailable for: {module.name}"
                )
            else:
                module.vram = Megabyte(capacity=gpu.apple_gpu.unified_memory_mb)

                apple_info = AppleExtendedGPUInfo()
                apple_info.gpu_core_count = gpu.apple_gpu.core_count
                apple_info.performance_shader_count = gpu.apple_gpu.gpu_perf_shaders
                apple_info.gpu_gen = gpu.apple_gpu.gpu_gen
                module.apple_gpu_info = apple_info

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
