import subprocess

from src.pysysinfo.dumps.mac.ioreg import corefoundation_to_native, IORegistryEntryCreateCFProperties, \
    IORegistryEntryFromPath, kIOMasterPortDefault, kNilOptions
from CoreFoundation import kCFAllocatorDefault
from src.pysysinfo.models.memory_models import MemoryInfo
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus


def fetch_memory_info() -> MemoryInfo:

    memory_info = MemoryInfo()
    """
    Memory Module Information, can only work on Intel and AMD machines.
    Does not work on Apple Silicon, because the modules are part of the SoC, and the info we need is not exposed.
    """
    arch = subprocess.check_output(["uname", "-m"]).decode()
    """
    Output:
    x86_64 for late-model Intel Macs
    i386 for earlier Intel Macs
    arm64 for Apple Silicon
    """
    if "arm" in arch.lower():
        memory_info.status = FailedStatus()
        return memory_info

    interface = corefoundation_to_native(
        IORegistryEntryCreateCFProperties(
            IORegistryEntryFromPath(kIOMasterPortDefault, b"IODeviceTree:/memory"),
            None,
            kCFAllocatorDefault,
            kNilOptions,
        )
    )[1]
    if not interface:
        memory_info.status = FailedStatus()
        return memory_info

    modules = []
    part_no = []
    dimm_types = []
    slot_names = []
    dimm_speeds = []
    dimm_manuf = []
    dimm_capacities = []
    sizes = []
    length = None

    print(interface)
    # print(interface.keys())
    # print(interface.values())

    for prop in interface:
        val = interface[prop]

        if not length and "part-number" not in prop:
            # --> [MEMORY]: No length specified for this RAM module – critical! — (IOKit/Memory)"
            pass

        if type(val) == bytes and length is int:
            if "reg" in prop.lower():
                readable = [
                    round(n * 0x010000 / 0x10)
                    for n in val.replace(b"\x00", b"")
                ]

                for i in range(length):
                    try:
                        # Converts non-0 values from the 'reg' property
                        # into readable integer values representing the memory capacity.
                        sizes.append(
                            readable[i]
                        )
                    except Exception as e:
                        memory_info.status = PartialStatus()
                        break

            else:
                try:
                    val = [
                        x.decode()
                        for x in val.split(b"\x00")
                        if type(x) == bytes and x.decode().strip()
                    ]
                except Exception as e:
                    # --> [MEMORY]: Failed to decode bytes of RAM module – critical! — (IOKit/Memory)
                    continue

        if "part-number" in prop:
            length = len(val)

            for i in range(length):
                part_no.append(val[i])

        else:
            for i in range(length):
                key = ""
                value = None

                if "dimm-types" in prop.lower():
                    key = "Type"
                    value = val[i]
                    dimm_types.append(val[i])

                elif "slot-names" in prop.lower():
                    key = "Slot"
                    try:
                        bank, channel = val[i].split("/")

                        value = {"Bank": bank, "Channel": channel}
                        slot_names.append(value)
                    except Exception as e:
                        # --> [MEMORY]: Failed to obtain location of current RAM module – ignoring! — (IOKit/Memory)"
                        pass

                elif "dimm-speeds" in prop.lower():
                    key = "Frequency (MHz)"
                    value = val[i]
                    dimm_speeds.append(value)

                elif "dimm-manufacturer" in prop.lower():
                    key = "Manufacturer"
                    value = val[i]
                    dimm_manuf.append(value)

                elif "reg" in prop.lower():
                    # --> [MEMORY]: Obtained capacity size (in MBs) of current RAM module! — (IOKit/Memory)",
                    key = "Capacity"
                    value = f"{sizes[i]}MB"
                    dimm_capacities.append(value)

    print(part_no)
    print(dimm_types)
    print(dimm_speeds)
    print(dimm_manuf)
    print(dimm_capacities)
    print(sizes)
    print(slot_names)

    return memory_info
