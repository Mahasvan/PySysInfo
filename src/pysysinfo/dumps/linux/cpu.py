import re
import subprocess

from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus


def fetch_arm_cpu_info(raw_cpu_info: str) -> CPUInfo:
    cpu_info = CPUInfo()

    cpu_info.architecture = "ARM"

    model = re.search(r"(?<=Hardware\t: ).+(?=\n)", raw_cpu_info)
    model_alt = re.search(r"Model\t+: (.+)(?=\n)", raw_cpu_info)

    if model:
        cpu_info.model_name = model.group(0)
    elif model_alt:
        cpu_info.model_name = model_alt.group(1)
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find model name")

    arm_version = re.search(r"(?<=CPU architecture: ).+(?=\n)", raw_cpu_info)
    if arm_version:
        cpu_info.arch_version = arm_version.group(0)
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find architecture")

    try:
        threads = raw_cpu_info.count("processor")
        cpu_info.threads = threads
    except Exception as e:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append(str(e))

    # nothing more can be retrieved from /proc/cpuinfo for ARM
    return cpu_info


def fetch_x86_cpu_info(raw_cpu_info: str) -> CPUInfo:
    cpu_info = CPUInfo()

    cpu_info.architecture = "x86"

    info_lines = [x for x in raw_cpu_info.split("\n\n") if x.strip("\n")]

    # CPU Info is enumerated as many times as there are CPU Threads.
    # To get the info, we only need to parse the first entry - i.e. the first CPU Thread
    cpu_lines = info_lines[0]

    model = re.search(r"(?<=model name\t: ).+(?=\n)", cpu_lines)
    if model:
        model = model.group(0)
        cpu_info.model_name = model
        vendor = "intel" if "intel" in model.lower() else "amd" if "amd" in model.lower() else "unknown"
        cpu_info.vendor = vendor
    else:
        cpu_info.status = PartialStatus(messages=cpu_info.status.messages)
        cpu_info.status.messages.append("Could not find model name")


    # The CPU flags are in the format of "flags : sse sse2 sse3 ssse3 sse4_1 sse4_2 lm"
    flags = re.search(r"(?<=flags\t\t: ).+(?=\n)", cpu_lines)
    if flags:
        flags = flags.group(0)
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
    cores = re.search(r"(?<=cpu cores\t: ).+(?=\n)", cpu_lines)

    try:
        if cores:
            cpu_info.cores = int(cores.group(0))
        else:
            cpu_info.status = PartialStatus()
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
        cpu_info.status = FailedStatus(messages=["Could not open /proc/cpuinfo"])
        # raise e
        return cpu_info

    if not raw_cpu_info:
        cpu_info.status = FailedStatus(messages=["/proc/cpuinfo has no content"])
        return cpu_info

    architecture = subprocess.run(['uname', '-m'], capture_output=True, text=True)

    if ("aarch64" in architecture.stdout) or ("arm" in architecture.stdout):
        return fetch_arm_cpu_info(raw_cpu_info)

    return fetch_x86_cpu_info(raw_cpu_info)

    # todo: get CPU codename from CodenameManager
