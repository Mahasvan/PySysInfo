from src.pysysinfo.dumps.linux.linux_dump import LinuxHardwareManager


lhm = LinuxHardwareManager()

lhm.fetch_cpu_info()

print(lhm.info)