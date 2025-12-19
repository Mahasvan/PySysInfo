import json

from src.pysysinfo.dumps.mac.mac_dump import MacHardwareManager
from src.pysysinfo.dumps.mac.memory import fetch_memory_info

lhm = MacHardwareManager()

lhm.fetch_cpu_info()
lhm.fetch_memory_info()
lhm.fetch_storage_info()

# fetch_memory_info()

json_data = json.loads(lhm.info.model_dump_json())

with open("response.json", "w") as f:
    json.dump(json_data, f, indent=2)

print(json.dumps(json_data, indent=2))