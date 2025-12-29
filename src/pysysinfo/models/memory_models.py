from typing import List, Optional

from pydantic import BaseModel
from pysysinfo.models.component_model import ComponentInfo
from pysysinfo.models.size_models import StorageSize, Kilobyte


class MemoryModuleSlot(BaseModel):
    channel: str = ""
    bank: str = ""


class MemoryModuleInfo(BaseModel):
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    # DDR4/DDR5/etc.
    type: Optional[str] = None
    capacity: Optional[StorageSize] = None
    frequency_mhz: Optional[int] = None
    slot: Optional[MemoryModuleSlot] = None
    supports_ecc: Optional[bool] = None


class MemoryInfo(ComponentInfo):
    modules: List[MemoryModuleInfo] = []
