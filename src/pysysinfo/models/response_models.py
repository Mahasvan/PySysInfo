from typing import List

from pydantic import BaseModel

from src.pysysinfo.models.success_models import StatusModel, SuccessStatus

class ComponentInfo(BaseModel):
    status: StatusModel = SuccessStatus()

class CPUInfo(ComponentInfo):
    model_name: str = ""
    vendor: str = ""
    flags: List[str] = []
    cores: int = -1
    threads: int = -1

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


class HardwareInfo(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo

class LinuxHardwareInfo(HardwareInfo):
    pass
