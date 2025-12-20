from typing import List, Optional

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo
from src.pysysinfo.models.size_models import StorageSize, Kilobyte


class MemoryModuleSlot(BaseModel):
    channel: str = ""
    bank: str = ""

class MemoryModuleInfo(BaseModel):
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    type: Optional[str] = None
    capacity: Optional[StorageSize] = None
    frequency_mhz: Optional[int] = None
    slot: Optional[MemoryModuleSlot] = None

class MemoryInfo(ComponentInfo):
    modules: List[MemoryModuleInfo] = []
