from pysysinfo.dumps.linux.cpu import fetch_cpu_info
from pysysinfo.dumps.linux.graphics import fetch_graphics_info
from pysysinfo.dumps.linux.memory import fetch_memory_info
from pysysinfo.dumps.linux.storage import fetch_storage_info
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.info_models import CPUInfo, LinuxHardwareInfo, MemoryInfo
from pysysinfo.models.info_models import HardwareManagerInterface
from pysysinfo.models.storage_models import StorageInfo


class LinuxHardwareManager(HardwareManagerInterface):
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Linux using the `sysfs` pseudo file system.

    https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html
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
