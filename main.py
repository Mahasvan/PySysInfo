import json

from src.pysysinfo.dumps.windows.windows_dump import WindowsHardwareManager
import time

start_time = time.time()
lhm = WindowsHardwareManager()

lhm.fetch_cpu_info()
lhm.fetch_memory_info()
# lhm.fetch_storage_info()
end_time = time.time()
print(f"Time taken: {end_time - start_time} seconds")
# fetch_memory_info()

json_data = json.loads(lhm.info.model_dump_json())

# with open("response.json", "w") as f:
    # json.dump(json_data, f, indent=2)

print(json.dumps(json_data, indent=2))
# print("done")