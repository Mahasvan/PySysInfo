from typing import Optional, List

from pydantic import BaseModel, Field
from pysysinfo.models.component_model import ComponentInfo
from pysysinfo.models.size_models import StorageSize


class GPUInfo(BaseModel):
    #: This is the GPU's name
    model: Optional[str] = None

    #: This is the hexadecimal number that identifies the manufacturer of the GPU.
    #: Format: ``0xPQRS``
    vendor_id: Optional[str] = None

    #: This is the hexadecimal number that identifies the GPU model.
    #: Format: ``0xPQRS``
    device_id: Optional[str] = None

    #: GPU vendor. ``NVIDIA``, for example.
    manufacturer: Optional[str] = None

    #: The manufacturer of the GPU. For example, it may be ``Lenovo`` on a Thinkpad.
    subsystem_manufacturer: Optional[str] = None
    #: The model name given by the subsystem manufacturer.
    subsystem_model: Optional[str] = None

    #: ACPI device path, e.g. ``\\_SB.PC00.RP05.PXSX``.
    acpi_path: Optional[str] = None
    #: PCI path from the firmware tree, e.g. ``PciRoot(0x0)/Pci(0x1C,0x5)/Pci(0x0,0x0)``.
    pci_path: Optional[str] = None

    #: Number of lanes that the GPU occupies on the PCIe bus.
    pcie_width: Optional[int] = None
    #: PCIe generation supported by the GPU.
    pcie_gen: Optional[int] = None
    #: Total VRAM available on the GPU.
    vram: Optional[StorageSize] = None
    #: Only for Apple Silicon GPUs: Number of GPU cores.
    #: ``null`` on all other platforms.
    apple_gpu_core_count: Optional[int] = None
    #: Only for Apple Silicon GPUs: Number of Neural Engine Cores.
    #: ``null`` on all other platforms.
    apple_neural_core_count: Optional[int] = None


class GraphicsInfo(ComponentInfo):
    #: List of GPU modules present in the system.
    modules: List[GPUInfo] = Field(default_factory=list)
