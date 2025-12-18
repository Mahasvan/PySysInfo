from typing import List

from pydantic import BaseModel

from src.pysysinfo.models.success_models import FailedStatus, StatusModel, SuccessStatus


class HardwareInfo(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo

class LinuxHardwareInfo(HardwareInfo):
    pass

class ComponentInfo(BaseModel):
    status: StatusModel = SuccessStatus()

class CPUInfo(ComponentInfo):
    model_name: str = ""
    vendor: str = ""
    flags: List[str] = []
    cores: int = -1
    threads: int = -1

class MemoryInfo(ComponentInfo):
    pass