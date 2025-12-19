import json

from src.pysysinfo.dumps.linux.linux_dump import LinuxHardwareManager


lhm = LinuxHardwareManager()

lhm.fetch_cpu_info()
lhm.fetch_memory_info()
lhm.fetch_storage_info()

json_data = json.loads(lhm.info.model_dump_json())

with open("response.json", "w") as f:
    json.dump(json_data, f, indent=2)

print(json.dumps(json_data, indent=2))