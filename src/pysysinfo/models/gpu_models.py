from typing import Optional, List

from pydantic import BaseModel
from pysysinfo.models.component_model import ComponentInfo
from pysysinfo.models.size_models import StorageSize


class GPUInfo(BaseModel):
    model: Optional[str] = None

    vendor_id: Optional[str] = None
    device_id: Optional[str] = None

    manufacturer: Optional[str] = None
    subsystem_manufacturer: Optional[str] = None
    subsystem_model: Optional[str] = None

    acpi_path: Optional[str] = None
    pci_path: Optional[str] = None

    pcie_width: Optional[int] = None
    pcie_gen: Optional[int] = None
    vram: Optional[StorageSize] = None

    apple_gpu_core_count: Optional[int] = None
    apple_neural_core_count: Optional[int] = None
    pass


class GraphicsInfo(ComponentInfo):
    modules: List[GPUInfo] = []
