from typing import Optional, List

from pydantic import BaseModel, Field

from pysysinfo.models.component_model import ComponentInfo

class ResolutionInfo(BaseModel):
    """Resolution information for a Display."""

    #: Horizontal resolution in pixels.
    width: Optional[int] = None

    #: Vertical resolution in pixels.
    height: Optional[int] = None

    #: Refresh rate in Hz.
    refresh_rate: Optional[int] = None

class DisplayModuleInfo(BaseModel):
    """Information for one Display is stored here"""

    # Name / model
    name: Optional[str] = None
    
    # Parent GPU driving this display
    parent_gpu: Optional[str] = None
    
    # Device ID
    device_id: Optional[str] = None
    
    # Hardware ID
    hardware_id: Optional[str] = None
    
    # The current resolution data
    resolution: Optional[ResolutionInfo] = Field(default_factory=ResolutionInfo)

    # Vendor ID
    vendor_id: Optional[str] = None
    
    # Product ID
    product_id: Optional[str] = None
    
    # Serial Number
    serial_number: Optional[str] = None
    
    # Manufacturer (3-letter code)
    manufacturer_code: Optional[str] = None

class DisplayInfo(ComponentInfo):
    """Contains list of ``DisplayModuleInfo`` objects."""

    #: List of GPU modules present in the system.
    modules: List[DisplayModuleInfo] = Field(default_factory=list)
