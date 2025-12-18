import os
import re
import subprocess

from src.pysysinfo.models.response_models import CPUInfo, LinuxHardwareInfo, MemoryInfo
from src.pysysinfo.models.success_models import PartialStatus, SuccessStatus, FailedStatus


class LinuxHardwareManager:
    """
    Instance, implementing `DeviceManager`, for extracting system information
    from Linux using the `sysfs` pseudo file system.

    https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html
    """
    def __init__(self):
        self.info = LinuxHardwareInfo(
            cpu=CPUInfo(),
            memory=MemoryInfo()
        )

    def fetch_cpu_info(self):
        try:
            raw_cpu_info = open('/proc/cpuinfo').read()
            # raw_cpu_info = open("cpuinfo.txt", "r").read()
        except Exception as e:
            # todo: handle error using logger, dont interrupt execution
            self.info.cpu.status = FailedStatus()
            raise e

        architecture = subprocess.run(['uname', '-m'], capture_output=True, text=True)
        # architecture = subprocess.run(['echo', 'x86_64'], capture_output=True, text=True)

        if (architecture.stdout == "aarch64") or ("arm" in architecture.stdout):
            raise NotImplementedError

        if not raw_cpu_info:
            self.info.cpu.status = FailedStatus()
            return

        cpu_info = [x for x in raw_cpu_info.split("\n\n") if x.strip("\n")]

        # CPU Info is enumerated as many times as there are CPU Threads.
        # To get the info, we only need to parse the first entry - i.e. the first CPU Thread
        cpu = cpu_info[0]

        # the CPU's name is in the format of "model name : Intel Core iSomething Something"
        model = re.search(r"(?<=model name\t\: ).+(?=\n)", cpu)
        if model:
            model = model.group(0)
            self.info.cpu.model_name = model
        else:
            self.info.cpu.status = PartialStatus()

        # we can safely assume that the vendor is AMD, if it's not Intel
        vendor = "intel" if "intel" in model.lower() else "amd"
        self.info.cpu.vendor = vendor

        # The CPU flags are in the format of "flags : sse sse2 sse3 ssse3 sse4_1 sse4_2"
        flags = re.search(r"(?<=flags\t\t\: ).+(?=\n)", cpu)

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
        cores = re.search(r"(?<=cpu cores\t\: ).+(?=\n)", cpu)

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
        self.info.cpu.status = PartialStatus()

        # todo: get CPU codename from CodenameManager