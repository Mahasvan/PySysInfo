import plistlib
import subprocess

from src.pysysinfo.models.memory_models import MemoryInfo, MemoryModuleInfo, MemoryModuleSlot
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus
from src.pysysinfo.models.size_models import Megabyte


def fetch_memory_info():

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
        memory_info.status = FailedStatus("Memory Info Retrieval not supported on Apple Silicon")
        return memory_info

    """
    We get the output of ioreg as a Plist, and parse it using Python's Plist library.
    `-alw0` forces a Plist output
    `-p` is used to traverse registry over the IODeviceTree plane (IOService is default)
    """
    try:
        output = subprocess.check_output(["ioreg", "-alw0", "-p", "IODeviceTree"])
        # output = subprocess.check_output(["cat", "/Users/mahas/Downloads/tree.txt"])
        pl = plistlib.loads(output, fmt=plistlib.FMT_XML)

        children = pl["IORegistryEntryChildren"]
    except Exception as e:
        memory_info.status = FailedStatus("Failed to parse ioreg: " + str(e))
        return memory_info

    dimm_manufacturer = []
    dimm_part_numbers = []
    dimm_serial_number = []
    dimm_speeds = []
    dimm_sizes = []
    dimm_types = []
    ecc_enabled = False
    # todo: Add ECC Detection to other OSes, and the Schema
    dimm_slots = []

    for child in children:
        array = child["IORegistryEntryChildren"]
        for entry in array:
            if entry["IORegistryEntryName"] != "memory":
                continue

            # This is the dictionary entry we want to parse
            for k, v in entry.items():
                """
                Actual Key names:
                - dimm-manufacturer
                - dimm-part-number
                - dimm-serial-number
                - dimm-speeds
                - dimm-types
                - ecc-enabled
                - reg
                - slot-names
                
                We don't use exact matching in case there are some discrepancies across machines.
                Since we have to accumulate all properties in their own arrays anyway,
                and make the MemoryModuleInfo afterwards, there is no downsides to iterating through all keys.
                """
                # we have to exactly match reg, because it can incorrectly match keys like IORegXYZ
                if k.lower() == "reg":
                    """
                    This key contains the capacity of the RAM module.
                    
                    Sample output:
                    b'\x02\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00'
                    
                    This, split into the number of RAM modules, gives us a value.
                    The RAM Capacity is this value multiplied by 4096.
                    
                    For simplicity, we can drop all '\x00's, and only retain the non-zero values.
                    Then, multiply every 16-bit offset by 4096, to get an array of RAM Capacities.
                    
                    (n * 0x010000 / 0x10) is used to multiply n by 4096.
                    - 0x010000 is 65536.
                    - 0x10 is 16.
                    - The multiplier is 65536 / 16 = 4096. 
                    """
                    dimm_sizes.extend([round(n * 0x010000 / 0x10) for n in v.replace(b"\x00", b"")])


                if "manufacturer" in k.lower():
                    dimm_manufacturer.extend([x.decode() for x in v.split(b'\x00') if x.decode().strip()])

                if "part-number" in k.lower():
                    dimm_part_numbers.extend([x.decode() for x in v.split(b'\x00') if x.decode().strip()])

                if "serial-number" in k.lower():
                    dimm_serial_number.extend([x.decode() for x in v.split(b'\x00') if x.decode().strip()])

                if "speed" in k.lower():
                    dimm_speeds.extend([x.decode() for x in v.split(b'\x00') if x.decode().strip()])

                if "type" in k.lower():
                    dimm_types = [x.decode() for x in v.split(b'\x00') if x.decode().strip()]

                if "ecc-enabled" in k.lower():
                    ecc_enabled = v

                if "slot-name" in k.lower():
                    # print(v)
                    dimm_slots = [x.decode().split("/") for x in v.split(b'\x00') if x.decode().strip()]

    # print("Manufacturers:", dimm_manufacturer)
    # print("Part Numbers:", dimm_part_numbers)
    # print("Serial Numbers:", dimm_serial_number)
    # print("Speeds:", dimm_speeds)
    # print("Capacities:", dimm_sizes)
    # print("Types:", dimm_types)
    # print("ECC Enabled:", ecc_enabled)
    # print("Slot Names:", dimm_slots)

    n_modules = max([len(dimm_manufacturer), len(dimm_part_numbers), len(dimm_serial_number),
                     len(dimm_speeds), len(dimm_types), len(dimm_slots)])

    for i in range(n_modules):
        module = MemoryModuleInfo()
        try:
            module.manufacturer = dimm_manufacturer[i]
            module.part_number = dimm_part_numbers[i]
            module.type = dimm_types[i]
            module.capacity = Megabyte(capacity=dimm_sizes[i])
            module.slot = MemoryModuleSlot(
                channel=dimm_slots[i][0],
                bank=dimm_slots[i][1]
            )
            module.frequency_mhz = int(dimm_speeds[i].lower().rstrip("mhz"))
            memory_info.modules.append(module)

        except Exception as e:
            memory_info.status = PartialStatus()

    return memory_info
