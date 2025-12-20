from src.pysysinfo.models.info_models import WindowsHardwareInfo
from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.memory_models import MemoryInfo
from src.pysysinfo.models.disk_models import StorageInfo

import wmi
from src.pysysinfo.dumps.windows.cpu import fetch_cpu_info
from src.pysysinfo.dumps.windows.memory import fetch_memory_info

import time

class WindowsHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Windows using the Registry and WMI
    """

    def __init__(self):
        self.info = WindowsHardwareInfo(
            cpu=CPUInfo(),
            memory=MemoryInfo(),
            storage=StorageInfo()
        )
        self.wmi_instance = self.c = wmi.WMI()

    def fetch_cpu_info(self):
        pass
        self.info.cpu = fetch_cpu_info(self.wmi_instance)

    def fetch_memory_info(self):
        pass
        self.info.memory = fetch_memory_info()

    def fetch_storage_info(self):
        pass
    