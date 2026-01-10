import json
import os
import platform
import sys
import time

# Add src to path so we can import pysysinfo
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import pysysinfo

print("Version:", pysysinfo.__version__)

global_start_time = time.time()

if os.name == "nt":
    print("OS: Windows")
elif platform.system() == "Darwin":
    print("OS: Mac")
else:
    print("OS: Linux")

hm = pysysinfo.HardwareManager()

loading_end_time = time.time()

start_times = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
# CPU, Memory, Storage, Display, Network, Graphics, Total
end_times = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

start_times[0] = start_times[-1] = time.time() * 1000

hm.fetch_cpu_info()
end_times[0] = start_times[1] = time.time() * 1000

hm.fetch_memory_info()
end_times[1] = start_times[2] = time.time() * 1000

hm.fetch_storage_info()
end_times[2] = start_times[3] = time.time() * 1000

hm.fetch_display_info()
end_times[3] = start_times[4] = time.time() * 1000

hm.fetch_network_info()
end_times[4] = start_times[5] = time.time() * 1000

hm.fetch_graphics_info()
end_times[-2] = end_times[-1] = time.time() * 1000

# print(start_times)
# print(end_times)
# print("Loading:", (loading_end_time-global_start_time)*1000, "ms")
print("CPU:", end_times[0] - start_times[0], "ms")
print("Memory:", end_times[1] - start_times[1], "ms")
print("Storage:", end_times[2] - start_times[2], "ms")
print("Display:", end_times[3] - start_times[3], "ms")
print("Network:", end_times[4] - start_times[4], "ms")
print("Graphics:", end_times[-2] - start_times[-2], "ms")
print("Total:", end_times[-1] - start_times[-1], "ms")
#
json_data = json.loads(hm.info.model_dump_json())
#
# with open("response.json", "w") as f:
#     json.dump(json_data, f, indent=2)
#
print(json.dumps(json_data, indent=2))
# # print("done")
