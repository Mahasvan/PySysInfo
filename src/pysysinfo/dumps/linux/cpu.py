import re
import subprocess
from typing import Optional

from pysysinfo.models.cpu_models import CPUInfo
from pysysinfo.models.status_models import FailedStatus, PartialStatus


def fetch_cpu_cores() -> Optional[int]:
    try:
        result = subprocess.run(["lscpu", "-p"], capture_output=True, text=True).stdout
        lines = [x for x in result.splitlines() if not x.startswith("#")]
        # Format: CPU,Core,Socket,Node,,L1d,L1i,L2,L3
        core_ids = [x.split(",")[1] for x in lines]
        # The number of distinct Core IDs is the number of cores
        return len(set(core_ids))
    except Exception as e:
        return None


def fetch_arm_cpu_info(raw_cpu_info: str) -> CPUInfo:
    cpu_info = CPUInfo()

    cpu_info.architecture = "ARM"

    model = re.search(r"Hardware\s+:\s+(.+)", raw_cpu_info)
    model_alt = re.search(r"Model\s+:\s+(.+)", raw_cpu_info)

    if model:
        cpu_info.name = model.group(1)
    elif model_alt:
        cpu_info.name = model_alt.group(1)
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find model name")

    arm_version = re.search(r"CPU architecture:\s+(.+)", raw_cpu_info)
    if arm_version:
        cpu_info.arch_version = arm_version.group(1)
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find architecture")

    try:
        threads = len(re.findall(r"^processor\s+:", raw_cpu_info, re.MULTILINE))
        cpu_info.threads = threads
    except Exception as e:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append(str(e))

    cores = fetch_cpu_cores()
    if not cores:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find CPU cores")
    else:
        cpu_info.cores = cores

    # nothing more can be retrieved from /proc/cpuinfo for ARM
    return cpu_info


def fetch_x86_cpu_info(raw_cpu_info: str) -> CPUInfo:
    cpu_info = CPUInfo()

    cpu_info.architecture = "x86"

    info_lines = [x for x in raw_cpu_info.split("\n\n") if x.strip("\n")]

    # CPU Info is enumerated as many times as there are CPU Threads.
    # To get the info, we only need to parse the first entry - i.e. the first CPU Thread
    cpu_lines = info_lines[0]

    model = re.search(r"model name\s+:\s+(.+)", cpu_lines)
    if model:
        model = model.group(1)
        cpu_info.name = model
        vendor = "intel" if "intel" in model.lower() else "amd" if "amd" in model.lower() else "unknown"
        cpu_info.vendor = vendor
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find model name")

    # The CPU flags are in the format of "flags : sse sse2 sse3 ssse3 sse4_1 sse4_2 lm"
    flags = re.search(r"flags\s+:\s+(.+)", cpu_lines)
    if flags:
        flags = flags.group(1)
    else:
        flags = ""
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find feature flags")

    flags = [x.lower().strip() for x in flags.split(" ")]

    sse_flags = [
        flag.replace("_", ".").upper() for flag in flags
        if "sse" in flag.lower()
    ]

    if sse_flags:
        cpu_info.sse_flags = sse_flags
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find SSE flags")

    """
    If "lm" is in flags, then x86-64 Long Mode is supported
    Which means it's a 64-bit CPU
    https://superuser.com/questions/502605/is-my-cpu-32-bit-or-64-bit-output-from-lshw-lscpu-getconf-and-proc-cpuinfo
    """
    if "lm" in flags:
        cpu_info.bitness = 64
    else:
        cpu_info.bitness = 32

    # Cores are in the format of "cores : 6"
    cores = re.search(r"cpu cores\s+:\s+(.+)", cpu_lines)

    try:
        if cores:
            cpu_info.cores = int(cores.group(1))
        else:
            cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
            cpu_info.status.messages.append("Could not find cpu cores")
    except Exception as e:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find cpu cores")

    # The number of CPU Threads is the number of times the processor data is enumerated.
    cpu_info.threads = len(info_lines)

    return cpu_info


def fetch_cpu_info() -> CPUInfo:
    cpu_info = CPUInfo()

    # todo: Check if any of the regexes may suffer from string having two `\t`s
    try:
        raw_cpu_info = open('/proc/cpuinfo').read()
    except Exception as e:
        # todo: handle error using logger, dont interrupt execution
        cpu_info.status = FailedStatus("Could not open /proc/cpuinfo")
        # raise e
        return cpu_info

    if not raw_cpu_info:
        cpu_info.status = FailedStatus("/proc/cpuinfo has no content")
        return cpu_info

    architecture = subprocess.run(['uname', '-m'], capture_output=True, text=True)

    if ("aarch64" in architecture.stdout) or ("arm" in architecture.stdout):
        return fetch_arm_cpu_info(raw_cpu_info)

    return fetch_x86_cpu_info(raw_cpu_info)

    # todo: get CPU codename from CodenameManager
