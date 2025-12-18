from typing import List

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo


class DiskInfo(BaseModel):
    model: str = ""
    location: str = ""
    connector: str = ""
    type: str = ""
    device_id: str = ""
    vendor_id: str = ""
    pass

class StorageInfo(ComponentInfo):
    disks: List[DiskInfo] = []
