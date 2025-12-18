from typing import List

from pydantic import BaseModel

from src.pysysinfo.models.component_model import ComponentInfo


class MemorySize(BaseModel):
    capacity: int

class Kilobyte(MemorySize):
    capacity: int = 0
    unit: str = "KB"

class Megabyte(MemorySize):
    capacity: int = 0
    unit: str = "MB"

class MemoryModuleSlot(BaseModel):
    channel: str = ""
    bank: str = ""

class MemoryModuleInfo(BaseModel):
    manufacturer: str = ""
    part_number: str = ""
    type: str = ""
    capacity: MemorySize = Kilobyte()
    slot: MemoryModuleSlot = MemoryModuleSlot()

class MemoryInfo(ComponentInfo):
    modules: List[MemoryModuleInfo] = []
