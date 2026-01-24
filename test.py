from pysysinfo.dumps.mac.mac_dump import MacHardwareManager

hm = MacHardwareManager()

cpu = hm.fetch_display_info()

print(cpu.model_dump_json(indent=2))
