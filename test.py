from src.hwprobe import HardwareManager

hm = HardwareManager()

hardware = hm.fetch_network_info()
print(hardware.model_dump_json(indent=2))