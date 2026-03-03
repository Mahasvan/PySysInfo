from src.pysysinfo.dumps.mac.mac_dump import MacHardwareManager

hm = MacHardwareManager()

graphics = hm.fetch_graphics_info()

print(graphics.model_dump_json(indent=2))
