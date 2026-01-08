from typing import List, Optional

from pydantic import BaseModel, Field
from pysysinfo.models.component_model import ComponentInfo

class NICInfo(BaseModel):
    device_id: Optional[str] = None
    vendor_id: Optional[str] = None
    acpi_path: Optional[str] = None
    pci_path: Optional[str] = None
    manufacturer: Optional[str] = None
    # The underlying network controller model
    controller_model: Optional[str] = None

class NetworkInfo(ComponentInfo): 
    modules: List[NICInfo] = Field(default_factory=list)