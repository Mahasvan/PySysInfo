from pydantic import BaseModel

from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.gpu_models import GraphicsInfo
from src.pysysinfo.models.memory_models import MemoryInfo
from src.pysysinfo.models.storage_models import StorageInfo


class HardwareInfo(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo
    storage: StorageInfo
    graphics: GraphicsInfo

class LinuxHardwareInfo(HardwareInfo):
    pass

class MacHardwareInfo(HardwareInfo):
    pass

class WindowsHardwareInfo(HardwareInfo):
    pass
