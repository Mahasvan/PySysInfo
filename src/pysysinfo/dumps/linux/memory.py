import os
import subprocess

from src.pysysinfo.dumps.linux.dmi_decode import get_string_entry, MEMORY_TYPE
from src.pysysinfo.models.memory_models import MemoryInfo, MemoryModuleSlot, MemoryModuleInfo
from src.pysysinfo.models.status_models import PartialStatus, FailedStatus
from src.pysysinfo.models.size_models import Megabyte, Kilobyte

def fetch_memory_info() -> MemoryInfo:
    memory_info = MemoryInfo()

    if not os.path.isdir("/sys/firmware/dmi/entries"):
        memory_info.status = FailedStatus("The /sys/firmware/dmi/entries directory doesn't exist")
        return memory_info

    """
    DMI Documentation: 
    SMBIOS Specification - Section 7.18 - Memory Device (Type 17)
    - https://www.dmtf.org/sites/default/files/standards/documents/DSP0134_3.9.0.pdf
    Other noteworthy mentions:
    - https://android.googlesource.com/kernel/common/+/android-trusty-3.10/Documentation/ABI/testing/sysfs-firmware-dmi
    - https://linux.die.net/man/8/dmidecode
    """
    # DMI entries relating to memory are of type 5,6,16, or 17
    # Memory _Module_ entries are of type 17, this is what we want to iterate over

    dmi_entries = os.scandir("/sys/firmware/dmi/entries")
    memory_dmi_types = "17-"
    parent_dirs = [p for p in dmi_entries if p.path.split("/")[-1].startswith(memory_dmi_types)]
    for parent_dir in parent_dirs:
        module = MemoryModuleInfo()
        # Attempt to get Part Number
        try:
            value = subprocess.check_output(
                [
                    "cat",
                    f"{parent_dir.path}/raw",
                ]
            )
            if "dimm" in value.upper().decode("latin-1").strip().lower():
                length_field = value[0x1]
                strings = value[length_field:len(value)].split(b'\0')

                """
                Obtains the value at offset 1Ah, which indicates at which index, pre-sanitization,
                in the `strings` list the real string value is stored.

                Which is: `strings[value[0x1A] - 1]`, after obtaining it, it decodes it to `ascii`.

                Special thanks to [Quist](https://github.com/nadiaholmquist) for this.
                """

                part_no = get_string_entry(strings, value[0x1A]).strip()
                module.part_number = part_no
        except subprocess.CalledProcessError as e:
            # todo: Need SUDO for this. Mention this in the Log
            memory_info.status = FailedStatus("Unable to open /sys/firmware/dmi/entries. Are you root?")
            return memory_info

        except Exception as e:
            memory_info.status = PartialStatus(messages=memory_info.status.messages)
            memory_info.status.messages.append("Reading DMI Entries: " + str(e))
            continue

        # Redefining here in case somehow it gets referenced before assignment
        length_field = value[0x1]
        strings = value[length_field:len(value)].split(b'\0')

        # Attempt to get DIMM type
        try:
            # DIMM type value is stored at offset 12h
            module.type = MEMORY_TYPE[value[0x12]]
        except Exception as e:
            memory_info.status = PartialStatus(messages=memory_info.status.messages)
            memory_info.status.messages.append("DIMM Type: " + str(e))
            continue

        # Attempt to obtain DIMM Location
        try:
            module.slot = MemoryModuleSlot(
                channel=get_string_entry(strings, value[0x10]),
                bank=get_string_entry(strings, value[0x11])
            )
        except Exception as e:
            memory_info.status = PartialStatus(messages=memory_info.status.messages)
            memory_info.status.messages.append("DIMM Location: " + str(e))
            continue

        # Attempt to obtain manufacturer
        try:
            module.manufacturer = get_string_entry(strings, value[0x17])
        except Exception as e:
            memory_info.status = PartialStatus(messages=memory_info.status.messages)
            memory_info.status.messages.append("DIMM Manufacturer: " + str(e))
            continue

        # Attempt to obtain capacity

        """
        Looks at the 2 bytes at offset 0Ch to determine its size;
        in case the value of these 2 bytes is equal to 0x7FFF, it looks at the 4 bytes
        at the Extended Size, which is at offset 1Ch.

        In case the value at offset 0Ch is equal to 0xFFFF,
        it would mean that the size is unknown.
        """

        """
        2 bytes, at offset 0Ch
        
        We convert it into an integer from the bytes values, specifying
        that it is in LE (little endian) format.
        
        Meaning, it will properly accommodate the values to represent its BE (big endian)
        value in the end.
        
        For example,
            (  Little  )  (   Big   )
            '\x00\x10' -> '\x10\x00'
            
        Finally, '\x10\x00' will yield `4096` in decimal (0x1000 in hexadecimal);
        which is correct. This was done on a system with 4x4GB memory modules.
        
        Aka, 4x4096MB modules, in this case--since the 15th bit value is `0`, 
        meaning it's represented in MB, and not KB.
        """

        try:
            size = int.from_bytes(value[0x0C:0x0E], "little")
            if size == 0xFFFF:
                # Unknown size
                memory_info.status = PartialStatus(messages=memory_info.status.messages)
                memory_info.status.messages.append("Unknown DIMM Size")
                continue

            if size == 0x7FFF:
                # 4 bytes, at offset 1Ch
                size = int(
                    "".join(
                        reversed(value.hex()[0x1C: 0x1C + 0x4])),
                    base=16
                )

            if (size >> 15) & 1 == 0:
                # Size is in Megabytes
                module.capacity = Megabyte(capacity=size)
            else:
                # Size is in Kilobytes
                module.capacity = Kilobyte(capacity=size)

        except Exception as e:
            print(e)
            memory_info.status = PartialStatus(messages=memory_info.status.messages)
            memory_info.status.messages.append("DIMM Capacity: " + str(e))
            continue

        # Now we attempt to check if the memory has ECC support
        """
        In a memory module with Data Width 64 bits, there are 8 more bits with an error correcting code. 
        so, the Total Width would be 64+8 = 72 bits.
        
        We can check the difference between DataWidth and TotalWidth, and equate it to DataWidth/8.
        This is to account for dual channel memory sometimes being reported as 
        128 bit DataWidth, and 144 bit TotalWidth.
        """
        total_width = int.from_bytes(value[0x08:0x0A], "little")
        data_width = int.from_bytes(value[0x0A:0x0C], "little")

        print("Total Width: " + str(total_width))
        print("DataWidth: " + str(data_width))

        if total_width - data_width == data_width//8:
            module.supports_ecc = True
        else:
            module.supports_ecc = False

        # Now we attempt to check the frequency
        """
        The speed of the RAM module (in MT/s) is stored in the offset 0x15 to 0x17.
        if the value of these 4 bytes is 0x0000, then the speed is unknown.
        If the value is 0xFFFF, then the speed is in the Extended Speed field,
        which is in the offset 0x54 to 0x58
        """
        ram_speed = int.from_bytes(value[0x15:0x17], "little")
        if ram_speed == 0xFFFF:
            ram_speed = int.from_bytes(value[0x54:0x58], "little")
        print("RAM Speed: " + str(ram_speed))

        module.frequency_mhz = ram_speed

        memory_info.modules.append(module)

    return memory_info
