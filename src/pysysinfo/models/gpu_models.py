from typing import Optional, List

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo

class GPUInfo(BaseModel):

    model: Optional[str] = None
    manufacturer: Optional[str] = None

    acpi_path: Optional[str] = None
    pci_path: Optional[str] = None

    # HDD/SSD
    type: Optional[str] = None

    device_id: Optional[str] = None
    vendor_id: Optional[str] = None

    pass

class GraphicsInfo(ComponentInfo):
    modules: List[GPUInfo] = []

