import json
import os

import time
import platform

global_start_time = time.time()

if os.name == "nt":
    print("OS: Windows")
    from src.pysysinfo.dumps.windows.windows_dump import WindowsHardwareManager
    lhm = WindowsHardwareManager()
elif platform.system() == "Darwin":
    print("OS: Mac")
    from src.pysysinfo.dumps.mac.mac_dump import MacHardwareManager
    lhm = MacHardwareManager()
else:
    print("OS: Linux")
    from src.pysysinfo.dumps.linux.linux_dump import LinuxHardwareManager
    lhm = LinuxHardwareManager()

start_times = [0.0, 0.0, 0.0, 0.0]
# CPU, Memory, Storage, Total
start_times[0] = start_times[-1] = time.time() * 1000
end_times = [0.0, 0.0, 0.0, 0.0]

lhm.fetch_cpu_info()
end_times[0] = start_times[1] = time.time() * 1000

lhm.fetch_memory_info()
end_times[1] = start_times[2] = time.time() * 1000

lhm.fetch_storage_info()
end_times[2] = end_times[-1] = time.time() * 1000

# print(start_times)
# print(end_times)
print("CPU:", end_times[0] - start_times[0], "ms")
print("Memory:", end_times[1] - start_times[1], "ms")
print("Storage:", end_times[2] - start_times[2], "ms")
print("Total:", end_times[3] - start_times[3], "ms")

#
json_data = json.loads(lhm.info.model_dump_json())
#
# with open("response.json", "w") as f:
#     json.dump(json_data, f, indent=2)
#
print(json.dumps(json_data, indent=2))
# # print("done")