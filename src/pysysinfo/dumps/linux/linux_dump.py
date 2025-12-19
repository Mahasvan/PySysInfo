from src.pysysinfo.dumps.linux.cpu import fetch_cpu_info
from src.pysysinfo.dumps.linux.memory import fetch_memory_info
from src.pysysinfo.dumps.linux.storage import fetch_storage_info
from src.pysysinfo.models.disk_models import StorageInfo
from src.pysysinfo.models.info_models import CPUInfo, LinuxHardwareInfo, MemoryInfo


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
            storage=StorageInfo()
        )

    def fetch_cpu_info(self):
        self.info.cpu = fetch_cpu_info()

    def fetch_memory_info(self):
        self.info.memory = fetch_memory_info()

    def fetch_storage_info(self):
        self.info.storage = fetch_storage_info()
