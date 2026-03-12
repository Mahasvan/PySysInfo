from src.pysysinfo.core.mac.mac_dump import MacHardwareManager

hm = MacHardwareManager()

hardware = hm.fetch_network_info()
print(hardware.model_dump_json(indent=2))