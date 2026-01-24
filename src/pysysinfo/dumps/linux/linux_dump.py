from pysysinfo.dumps.linux.cpu import fetch_cpu_info
from pysysinfo.dumps.linux.display import fetch_display_info
from pysysinfo.dumps.linux.graphics import fetch_graphics_info
from pysysinfo.dumps.linux.memory import fetch_memory_info
from pysysinfo.dumps.linux.storage import fetch_storage_info
from pysysinfo.models.display_models import DisplayInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.info_models import (
    CPUInfo,
    HardwareInfo,
    HardwareManagerInterface,
    LinuxHardwareInfo,
    MemoryInfo,
)
from pysysinfo.models.storage_models import StorageInfo


class LinuxHardwareManager(HardwareManagerInterface):
    """
    Uses the `sysfs` pseudo file system to extract info.
    """

    def __init__(self):
        self.info = LinuxHardwareInfo(
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

    def fetch_display_info(self) -> DisplayInfo:
        return fetch_display_info()
