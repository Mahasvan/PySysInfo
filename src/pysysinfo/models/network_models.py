from typing import List, Optional

from pydantic import BaseModel, Field
from pysysinfo.models.component_model import ComponentInfo

class NICInfo(BaseModel):
    # The underlying network controller model
    name: Optional[str] = None
    
    # Device ID
    device_id: Optional[str] = None
    
    # Vendor ID
    vendor_id: Optional[str] = None
    
    # ACPI path of NIC
    acpi_path: Optional[str] = None
    
    # PCI path of NIC
    pci_path: Optional[str] = None
    
    # Manufacturer
    manufacturer: Optional[str] = None

class NetworkInfo(ComponentInfo): 
    modules: List[NICInfo] = Field(default_factory=list)