from pysysinfo.dumps.windows.cpu import fetch_cpu_info
from pysysinfo.dumps.windows.graphics import fetch_graphics_info
from pysysinfo.dumps.windows.memory import fetch_memory_info
from pysysinfo.dumps.windows.storage import fetch_storage_info
from pysysinfo.models.cpu_models import CPUInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.info_models import HardwareManagerInterface
from pysysinfo.models.info_models import WindowsHardwareInfo
from pysysinfo.models.memory_models import MemoryInfo
from pysysinfo.models.storage_models import StorageInfo


class WindowsHardwareManager(HardwareManagerInterface):
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Windows using the Registry and WMI
    """

    def __init__(self):
        self.info = WindowsHardwareInfo(
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
