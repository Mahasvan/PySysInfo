from typing import Optional

from pydantic import BaseModel

from pysysinfo.models.audio_models import AudioInfo
from pysysinfo.models.baseboard_models import BaseboardInfo
from pysysinfo.models.cpu_models import CPUInfo
from pysysinfo.models.display_models import DisplayInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.memory_models import MemoryInfo
from pysysinfo.models.network_models import NetworkInfo
from pysysinfo.models.storage_models import StorageInfo


class HardwareInfo(BaseModel):
    cpu: Optional[CPUInfo] = None
    memory: Optional[MemoryInfo] = None
    storage: Optional[StorageInfo] = None
    graphics: Optional[GraphicsInfo] = None
    network: Optional[NetworkInfo] = None
    display: Optional[DisplayInfo] = None
    audio: Optional[AudioInfo] = None
    baseboard: Optional[BaseboardInfo] = None


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
