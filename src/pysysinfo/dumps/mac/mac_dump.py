from src.pysysinfo.dumps.mac.cpu import fetch_cpu_info
from src.pysysinfo.dumps.mac.memory import fetch_memory_info
from src.pysysinfo.dumps.mac.storage import fetch_storage_info
from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.disk_models import StorageInfo
from src.pysysinfo.models.info_models import MacHardwareInfo
from src.pysysinfo.models.memory_models import MemoryInfo


class MacHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from macOS using `sysctl` and IOreg
    """

    def __init__(self):
        self.info = MacHardwareInfo(
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