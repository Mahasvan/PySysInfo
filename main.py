from src.pysysinfo.dumps.linux.linux_dump import LinuxHardwareManager


lhm = LinuxHardwareManager()

lhm.fetch_cpu_info()
lhm.fetch_memory_info()
lhm.fetch_storage_info()

print(lhm.info)