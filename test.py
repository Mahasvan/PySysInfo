from pysysinfo.dumps.linux.linux_dump import LinuxHardwareManager

hm = LinuxHardwareManager()

cpu = hm.fetch_display_info()

print(cpu.model_dump_json(indent=2))
