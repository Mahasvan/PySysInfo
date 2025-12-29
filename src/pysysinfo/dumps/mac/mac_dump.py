from pysysinfo.dumps.mac.cpu import fetch_cpu_info
from pysysinfo.dumps.mac.graphics import fetch_graphics_info
from pysysinfo.dumps.mac.memory import fetch_memory_info
from pysysinfo.dumps.mac.storage import fetch_storage_info
from pysysinfo.models.cpu_models import CPUInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.info_models import HardwareInfo
from pysysinfo.models.info_models import HardwareManagerInterface
from pysysinfo.models.info_models import MacHardwareInfo
from pysysinfo.models.memory_models import MemoryInfo
from pysysinfo.models.storage_models import StorageInfo


class MacHardwareManager(HardwareManagerInterface):
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from macOS using `sysctl` and IOreg
    """

    def __init__(self):
        self.info = MacHardwareInfo(
            cpu=CPUInfo(),
            memory=MemoryInfo(),
            storage=StorageInfo(),
            graphics=GraphicsInfo(),
        )

    def fetch_cpu_info(self) -> CPUInfo:
        self.info.cpu = fetch_cpu_info()
        return self.info.cpu

    def fetch_memory_info(self) -> MemoryInfo:
        self.info.memory = fetch_memory_info()
        return self.info.memory

    def fetch_storage_info(self) -> StorageInfo:
        self.info.storage = fetch_storage_info()
        return self.info.storage

    def fetch_graphics_info(self) -> GraphicsInfo:
        self.info.graphics = fetch_graphics_info()
        return self.info.graphics

    def fetch_hardware_info(self) -> HardwareInfo:
        self.fetch_cpu_info()
        self.fetch_memory_info()
        self.fetch_storage_info()
        self.fetch_graphics_info()
        return self.info
