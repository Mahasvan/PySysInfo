from pysysinfo.dumps.windows.cpu import fetch_cpu_info
from pysysinfo.dumps.windows.graphics import fetch_graphics_info
from pysysinfo.dumps.windows.memory import fetch_memory_info
from pysysinfo.dumps.windows.storage import fetch_storage_info
from pysysinfo.dumps.windows.network import fetch_wmi_cmdlet_network_info
from pysysinfo.models.cpu_models import CPUInfo
from pysysinfo.models.gpu_models import GraphicsInfo
from pysysinfo.models.info_models import HardwareInfo
from pysysinfo.models.info_models import HardwareManagerInterface
from pysysinfo.models.info_models import WindowsHardwareInfo
from pysysinfo.models.memory_models import MemoryInfo
from pysysinfo.models.storage_models import StorageInfo
from pysysinfo.models.network_models import NetworkInfo


class WindowsHardwareManager(HardwareManagerInterface):
    """
    Uses Registry and WMI to extract info.
    """

    def __init__(self):
        self.info = WindowsHardwareInfo(
            cpu=CPUInfo(),
            memory=MemoryInfo(),
            storage=StorageInfo(),
            graphics=GraphicsInfo(),
            network=NetworkInfo()
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
    
    def fetch_network_info(self) -> NetworkInfo:
        self.info.network = fetch_wmi_cmdlet_network_info()
        return self.info.network

    def fetch_hardware_info(self) -> HardwareInfo:
        self.fetch_cpu_info()
        self.fetch_memory_info()
        self.fetch_storage_info()
        self.fetch_graphics_info()
        return self.info

