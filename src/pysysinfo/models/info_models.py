from typing import Optional

from pydantic import BaseModel

from pysysinfo.models.cpu_models import CPUInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.memory_models import MemoryInfo
from pysysinfo.models.storage_models import StorageInfo


class HardwareInfo(BaseModel):
    cpu: Optional[CPUInfo] = None
    memory: Optional[MemoryInfo] = None
    storage: Optional[StorageInfo] = None
    graphics: Optional[GraphicsInfo] = None

class LinuxHardwareInfo(HardwareInfo):
    pass

class MacHardwareInfo(HardwareInfo):
    pass

class WindowsHardwareInfo(HardwareInfo):
    pass

class HardwareManagerInterface:
    info: HardwareInfo

    def fetch_cpu_info(self) -> CPUInfo:
        pass
    def fetch_graphics_info(self) -> GraphicsInfo:
        pass
    def fetch_memory_info(self) -> MemoryInfo:
        pass
    def fetch_storage_info(self) -> StorageInfo:
        pass

