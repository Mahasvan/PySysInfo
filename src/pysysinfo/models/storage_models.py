from typing import List, Optional

from pydantic import BaseModel, Field

from pysysinfo.models.component_model import ComponentInfo
from pysysinfo.models.size_models import StorageSize


class DiskInfo(BaseModel):
    # Device Name
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    # Internal/External
    location: Optional[str] = None
    # PCIe/SCSI/etc.
    connector: Optional[str] = None
    # HDD/SSD
    type: Optional[str] = None

    device_id: Optional[str] = None
    vendor_id: Optional[str] = None
    size: Optional[StorageSize] = None
    pass


class StorageInfo(ComponentInfo):
    modules: List[DiskInfo] = Field(default_factory=list)
