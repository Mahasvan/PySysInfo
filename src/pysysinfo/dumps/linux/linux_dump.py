import os
import re
import subprocess

from src.pysysinfo.dumps.linux.dmi_decode import get_string_entry, MEMORY_TYPE
from src.pysysinfo.models.response_models import CPUInfo, LinuxHardwareInfo, MemoryInfo
from src.pysysinfo.models.memory_models import MemoryModuleInfo, MemoryModuleSlot
from src.pysysinfo.models.disk_models import DiskInfo, StorageInfo
from src.pysysinfo.models.status_models import PartialStatus, FailedStatus
from src.pysysinfo.models.storage_models import Megabyte, Kilobyte, Gigabyte


class LinuxHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Linux using the `sysfs` pseudo file system.

    https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html
    """

    def __init__(self):
        self.info = LinuxHardwareInfo(
            cpu=CPUInfo(),
            memory=MemoryInfo(),
            storage=StorageInfo()
        )

    def fetch_cpu_info(self):

        # todo: Check if any of the regexes may suffer from string having two `\t`s

        try:
            raw_cpu_info = open('/proc/cpuinfo').read()
        except Exception as e:
            # todo: handle error using logger, dont interrupt execution
            self.info.cpu.status = FailedStatus()
            raise e

        architecture = subprocess.run(['uname', '-m'], capture_output=True, text=True)

        if not raw_cpu_info:
            self.info.cpu.status = FailedStatus()
            return
        if ("aarch64" in architecture.stdout) or ("arm" in architecture.stdout):
            self.info.cpu.architecture = "ARM"
            model = re.search(r"(?<=Hardware\t: ).+(?=\n)", raw_cpu_info)
            if model:
                self.info.cpu.model_name = model.group(0)
            else:
                # If the first regex doesn't match, try an alternative pattern
                model_alt = re.search(r"Model\t+: (.+)(?=\n)", raw_cpu_info)
                if model_alt:
                    model_alt = model_alt.group(1)
                    self.info.cpu.model_name = model_alt
                else:
                    # if neither pattern matches, change Success to Partial status
                    self.info.cpu.status = PartialStatus()

            arm_version = re.search(r"(?<=CPU architecture: ).+(?=\n)", raw_cpu_info)
            if arm_version:
                self.info.cpu.version = arm_version.group(0)
            else:
                self.info.cpu.status = PartialStatus()

            try:
                threads = raw_cpu_info.count("processor")
                self.info.cpu.threads = threads
            except Exception as e:
                # todo: log this appropriately
                self.info.cpu.status = PartialStatus()

            # nothing more can be retrieved from /proc/cpuinfo for ARM
            return

        self.info.cpu.architecture = "x86_64"


        cpu_info = [x for x in raw_cpu_info.split("\n\n") if x.strip("\n")]

        # CPU Info is enumerated as many times as there are CPU Threads.
        # To get the info, we only need to parse the first entry - i.e. the first CPU Thread
        cpu = cpu_info[0]

        # the CPU's name is in the format of "model name : Intel Core iSomething Something"
        model = re.search(r"(?<=model name\t: ).+(?=\n)", cpu)
        if model:
            model = model.group(0)
            self.info.cpu.model_name = model
        else:
            self.info.cpu.status = PartialStatus()

        # we can safely assume that the vendor is AMD, if it's not Intel
        vendor = "intel" if "intel" in model.lower() else "amd"
        self.info.cpu.vendor = vendor

        # The CPU flags are in the format of "flags : sse sse2 sse3 ssse3 sse4_1 sse4_2"
        flags = re.search(r"(?<=flags\t\t: ).+(?=\n)", cpu)

        if flags:
            flags = flags.group(0)

        sse_flags = [
            flag.replace("_", ".").upper() for flag in flags.split(" ")
            if "sse" in flag.lower()
        ]

        if sse_flags:
            self.info.cpu.flags = sse_flags
        else:
            self.info.cpu.status = PartialStatus()

        # Cores are in the format of "cores : 6"
        cores = re.search(r"(?<=cpu cores\t: ).+(?=\n)", cpu)

        if cores:
            try:
                self.info.cpu.cores = int(cores.group(0))
            except Exception as e:
                self.info.cpu.status = PartialStatus()
                raise e
        else:
            self.info.cpu.status = PartialStatus()

        # The number of CPU Threads is the number of times the processor data is enumerated.
        self.info.cpu.threads = len(cpu_info)

        # todo: get CPU codename from CodenameManager

    def fetch_memory_info(self):
        if not os.path.isdir("/sys/firmware/dmi/entries"):
            self.info.memory.status = FailedStatus()
            return

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
                self.info.memory.status = FailedStatus()
                return
            except Exception as e:
                self.info.memory.status = PartialStatus()
                # todo: Log the error appropriately
                continue

            # Redefining here in case somehow it gets referenced before assignment
            length_field = value[0x1]
            strings = value[length_field:len(value)].split(b'\0')

            # Attempt to get DIMM type
            try:
                # DIMM type value is stored at offset 12h
                module.type = MEMORY_TYPE[value[0x12]]
            except Exception as e:
                # todo: Log appropriately
                self.info.memory.status = PartialStatus()
                continue

            # Attempt to obtain DIMM Location
            try:
                module.slot = MemoryModuleSlot(
                    channel=get_string_entry(strings, value[0x10]),
                    bank=get_string_entry(strings, value[0x11])
                )
            except Exception as e:
                self.info.memory.status = PartialStatus()
                continue
                # todo: Log appropriately

            # Attempt to obtain manufacturer
            try:
                module.manufacturer = get_string_entry(strings, value[0x17])
            except Exception as e:
                self.info.memory.status = PartialStatus()
                continue
                # todo: Log this appropriately

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
                    self.info.memory.status = PartialStatus()
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
                self.info.memory.status = PartialStatus()
                continue
                # todo: Log this appropriately

            self.info.memory.modules.append(module)

    def fetch_storage_info(self):
        # Storage Block Information is in /sys/block
        if not os.path.isdir("/sys/block"):
            self.info.disk.status = FailedStatus()
            return

        for folder in os.listdir("/sys/block"):
            disk = DiskInfo()

            path = f"/sys/block/{folder}"
            # todo: mmcblk detection e.g. eMMC storage
            try:
                if (not "nvme" in folder) and (not "sd" in folder):
                    continue

                # Check properties of block device
                model = open(f"{path}/device/model", "r").read().strip()

                if model:
                    disk.model = model
                else:
                    self.info.storage.status = PartialStatus()

                rotational = open(f"{path}/queue/rotational", "r").read().strip()
                removable = open(f"{path}/removable", "r").read().strip()

                # todo: USB block devices all report as HDDs?
                disk.type = (
                    "Solid State Drive (SSD)"
                    if rotational == "0"
                    else "Hard Disk Drive (HDD)"
                )

                disk.location = "Internal" if removable == "0" else "External"

                if "nvme" in folder:
                    disk.connector = "PCIe"
                    disk.type = "Non-Volatile Memory Express (NVMe)"

                    # Uses PCI vendor & device ids to get a vendor for the NVMe block device
                    disk.device_id = open(f"{path}/device/device/device",
                               "r").read().strip()
                    disk.vendor_id = open(f"{path}/device/device/vendor",
                               "r").read().strip()
                elif "sd" in folder:
                    # todo: Choose correct connector type for block devices that use the SCSI subsystem
                    disk.connector = "SCSI"
                    disk.vendor_id = open(f"{path}/device/vendor", "r").read().strip()
                else:
                    disk.connector = "Unknown"

                """
                Disk Size - Is the value in /sys/block/sda/size Multiplied by the Block Size
                In Linux, the block size is always considered as 512
                - https://github.com/torvalds/linux/blob/master/include/linux/types.h#L132
                """

                size = open(f"{path}/size", "r").read().strip()
                size_in_bytes = int(size) * 512
                disk.size = Megabyte(capacity=(size_in_bytes // 1024**2))

            except Exception as e:
                self.info.storage.status = PartialStatus()
                # todo: Log this properly

            self.info.storage.disks.append(disk)