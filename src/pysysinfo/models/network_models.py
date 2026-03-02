from typing import List, Optional

from pydantic import BaseModel, Field

from pysysinfo.models.component_model import ComponentInfo


class NICInfo(BaseModel):
    name: Optional[str] = None

    # TODO: Old Stuff: Need to revamp

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

    """New Stuff begins here"""
    interface: Optional[str] = None
    mac_address: Optional[str] = None
    type: Optional[str] = None
    ip_address: Optional[str] = None


class NetworkInfo(ComponentInfo):
    modules: List[NICInfo] = Field(default_factory=list)
