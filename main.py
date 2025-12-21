import json
import os

import time
import platform
start_time = time.time()
# if the current os is windows:
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


lhm.fetch_cpu_info()
lhm.fetch_memory_info()
lhm.fetch_storage_info()
end_time = time.time()
print(f"Time taken: {end_time - start_time} seconds")
#
json_data = json.loads(lhm.info.model_dump_json())
#
# with open("response.json", "w") as f:
#     json.dump(json_data, f, indent=2)
#
print(json.dumps(json_data, indent=2))
# # print("done")