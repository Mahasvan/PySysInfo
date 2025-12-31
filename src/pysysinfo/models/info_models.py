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
    """The hardware manager of every OS follows this structure."""

    #: Holds all data retrieved. Once any component's data is queried, the data is stored in it.
    info: HardwareInfo

    def fetch_cpu_info(self) -> CPUInfo:
        """Fetches CPU Information. Returns a :class:`pysysinfo.models.cpu_models.CPUInfo` object."""
        pass

    def fetch_graphics_info(self) -> GraphicsInfo:
        """Fetches GPU Information. Returns a :class:`pysysinfo.models.gpu_models.GraphicsInfo` object."""
        pass

    def fetch_memory_info(self) -> MemoryInfo:
        """Fetches RAM Information. Returns a :class:`pysysinfo.models.memory_models.MemoryInfo` object."""
        pass

    def fetch_storage_info(self) -> StorageInfo:
        """Fetches Disk Information. Returns a :class:`pysysinfo.models.storage_models.StorageInfo` object."""
        pass

    def fetch_hardware_info(self) -> HardwareInfo:
        """Fetches all hardware Information. Returns a :class:`pysysinfo.models.info_models.HardwareInfo` object."""
        pass
