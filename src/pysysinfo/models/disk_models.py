from typing import List, Optional

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo
from src.pysysinfo.models.storage_models import StorageSize


class DiskInfo(BaseModel):
    model: Optional[str] = None
    location: Optional[str] = None
    connector: Optional[str] = None
    type: Optional[str] = None
    device_id: Optional[str] = None
    vendor_id: Optional[str] = None
    size: Optional[StorageSize] = None
    pass

class StorageInfo(ComponentInfo):
    disks: List[DiskInfo] = []
