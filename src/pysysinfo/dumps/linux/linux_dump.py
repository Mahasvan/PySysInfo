from src.pysysinfo.dumps.linux.cpu import fetch_cpu_info
from src.pysysinfo.dumps.linux.gpu import fetch_gpu_info
from src.pysysinfo.dumps.linux.memory import fetch_memory_info
from src.pysysinfo.dumps.linux.storage import fetch_storage_info
from src.pysysinfo.models.gpu_models import GraphicsInfo
from src.pysysinfo.models.info_models import CPUInfo, LinuxHardwareInfo, MemoryInfo
from src.pysysinfo.models.storage_models import StorageInfo


class LinuxHardwareManager:
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

    def fetch_cpu_info(self):
        self.info.cpu = fetch_cpu_info()

    def fetch_memory_info(self):
        self.info.memory = fetch_memory_info()

    def fetch_storage_info(self):
        self.info.storage = fetch_storage_info()

    def fetch_graphics_info(self):
        self.info.graphics = fetch_gpu_info()