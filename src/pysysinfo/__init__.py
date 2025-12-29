import os
import platform

if os.name == "nt":
    from pysysinfo.dumps.windows.windows_dump import WindowsHardwareManager as HardwareManager
elif platform.system() == "Darwin":
    from pysysinfo.dumps.mac.mac_dump import MacHardwareManager as HardwareManager
else:
    from pysysinfo.dumps.linux.linux_dump import LinuxHardwareManager as HardwareManager

__all__ = ["HardwareManager"]
