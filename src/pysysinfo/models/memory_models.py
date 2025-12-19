from typing import List

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo
from src.pysysinfo.models.storage_models import StorageSize, Kilobyte


class MemoryModuleSlot(BaseModel):
    channel: str = ""
    bank: str = ""

class MemoryModuleInfo(BaseModel):
    manufacturer: str = ""
    part_number: str = ""
    type: str = ""
    capacity: StorageSize = Kilobyte()
    slot: MemoryModuleSlot = MemoryModuleSlot()

class MemoryInfo(ComponentInfo):
    modules: List[MemoryModuleInfo] = []
