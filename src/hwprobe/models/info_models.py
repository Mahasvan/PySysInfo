from typing import Optional

from pydantic import BaseModel

from hwprobe.models.audio_models import AudioInfo
from hwprobe.models.baseboard_models import BaseboardInfo
from hwprobe.models.cpu_models import CPUInfo
from hwprobe.models.display_models import DisplayInfo
from hwprobe.models.gpu_models import GraphicsInfo
from hwprobe.models.memory_models import MemoryInfo
from hwprobe.models.network_models import NetworkInfo
from hwprobe.models.storage_models import StorageInfo


class HardwareInfo(BaseModel):
    cpu: Optional[CPUInfo] = None
    memory: Optional[MemoryInfo] = None
    storage: Optional[StorageInfo] = None
    graphics: Optional[GraphicsInfo] = None
    network: Optional[NetworkInfo] = None


class LinuxHardwareInfo(HardwareInfo):
    pass


class MacHardwareInfo(HardwareInfo):
    pass


class WindowsHardwareInfo(HardwareInfo):
    pass


class HardwareManagerInterface:
    """The hardware manager of every OS follows this structure."""

    #: When any component's data is queried, the data is stored here.
    info: HardwareInfo

    def fetch_hardware_info(self) -> HardwareInfo:
        """Fetches all hardware Information."""

    pass

    def fetch_cpu_info(self) -> CPUInfo:
        """Fetches CPU Information."""
        pass

    def fetch_graphics_info(self) -> GraphicsInfo:
        """Fetches GPU Information."""
        pass

    def fetch_memory_info(self) -> MemoryInfo:
        """Fetches RAM Information."""
        pass

    def fetch_storage_info(self) -> StorageInfo:
        """Fetches Disk Information."""
        pass

    def fetch_network_info(self) -> NetworkInfo:
        """Fetches Network Information."""
        pass

    def fetch_display_info(self) -> DisplayInfo:
        """Fetches Display Information."""
        pass

    def fetch_audio_info(self) -> AudioInfo:
        """Fetches Audio Information."""
        pass

    def fetch_baseboard_info(self) -> BaseboardInfo:
        """Fetches Baseboard Information."""
        pass
