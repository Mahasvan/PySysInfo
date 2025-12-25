from typing import Optional, List

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo
from src.pysysinfo.models.size_models import StorageSize


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
    pass

class GraphicsInfo(ComponentInfo):
    modules: List[GPUInfo] = []

