import pysysinfo
from pysysinfo.models.status_models import StatusType

hm = pysysinfo.HardwareManager()

cpu = hm.fetch_cpu_info()

if cpu.status.type == StatusType.FAILED:
    print("Failed - Fatal issue(s) occurred:")
    for message in cpu.status.messages:
        print(message)

    exit(1) # Don't continue executing

elif cpu.status.type == StatusType.PARTIAL:
    print("Partial Error - Issue(s) occurred:")
    for message in cpu.status.messages:
        print(message)

    # Continue executing
    print(cpu.name)

else:
    # It is StatusType.SUCCESS
    print("Successfully retrieved info!")
    print(cpu.name)