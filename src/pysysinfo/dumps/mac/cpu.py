import subprocess

from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.status_models import PartialStatus, FailedStatus


def fetch_cpu_info() -> CPUInfo:
    cpu_info = CPUInfo()

    try:
        data = subprocess.check_output(["sysctl", "machdep.cpu"]).decode()
        """
        Sample output:
        machdep.cpu.cores_per_package: 8
        machdep.cpu.core_count: 8
        machdep.cpu.logical_per_package: 8
        machdep.cpu.thread_count: 8
        machdep.cpu.brand_string: Apple M3
        """
        # we split it into lines, and make a dictionary with key:value pairs
        data = {k:v for (k,v) in [x.split(": ") for x in data.splitlines()]}
    except Exception as e:
        cpu_info.status = FailedStatus()
        return cpu_info

    try:
        arch = subprocess.check_output(["uname", "-m"]).decode()
        """
        Output:
        x86_64 for late-model Intel Macs
        i386 for earlier Intel Macs
        arm64 for Apple Silicon
        """
    except Exception as e:
        cpu_info.status = FailedStatus()
        return cpu_info

    if "arm" in arch:
        cpu_info.architecture = "ARM"
        cpu_info.bitness = 64
    elif "i386" in arch or "x86" in arch:
        cpu_info.architecture = "x86"
    else:
        cpu_info.status = PartialStatus()

    try:
        bitness_64 = subprocess.check_output(["sysctl", "hw.cpu64bit_capable"]).decode()
        bitness_64 = True if bitness_64.split(": ")[1].strip() == "1" else False

        if bitness_64:
            cpu_info.bitness = 64
        else:
            cpu_info.bitness = 32

    except Exception as e:
        cpu_info.status = PartialStatus()

    if "machdep.cpu.brand_string" in data:
        cpu_info.model_name = data["machdep.cpu.brand_string"]
    else:
        cpu_info.status = PartialStatus()

    if "machdep.cpu.vendor" in data:
        """
        Common outputs:
        AuthenticAMD - AMD CPUs
        GenuineIntel - Intel CPUs
        This field doesnt exist for Apple M series CPUs
        """
        if "amd" in data["machdep.cpu.vendor"].lower():
            cpu_info.vendor = "AMD"
        elif "intel" in data["machdep.cpu.vendor"].lower():
            cpu_info.vendor = "Intel"
        else:
            # Python 3.9 won't run on PowerPC, so we can be sure that it's an Apple CPU
            # Apple Silicon machines usually dont have the machdep.cpu.vendor string
            # So, this branch will likely not execute. This is defined just in case.
            cpu_info.vendor = "Apple"
    elif "apple" in data["machdep.cpu.brand_string"].lower():
        # Apple Silicon devices do not have machdep.cpu.vendor defined.
        cpu_info.vendor = "Apple"

    # Apple Silicon machines do not have this field defined.
    # todo: check if we can get this info another way.
    if "machdep.cpu.features" in data:
        sse_features = [f.upper() for f in data["machdep.cpu.features"].split(" ") if "SSE" in f.upper()]
        if sse_features:
            cpu_info.sse_flags = sse_features
        else:
            cpu_info.status = PartialStatus()

    try:
        if "machdep.cpu.core_count" in data:
            cpu_info.cores = int(data["machdep.cpu.core_count"])
        else:
            cpu_info.status = PartialStatus()
        if "machdep.cpu.thread_count" in data:
            cpu_info.threads = int(data["machdep.cpu.thread_count"])
        else:
            cpu_info.status = PartialStatus()
    except Exception as e:
        cpu_info.status = PartialStatus()

    # Attempt to get ARM version
    """
    in macOS, ARM can be of version 8 or 9.
    We can differentiate between v8 and v9 based on the presence of v9 capabilities,
    such as SME and SME2. Apple has not implemented SVE2 capabilities to their CPUs, so we cannot use those. 
    """
    if "arm" in arch:
        try:
            SME_presence = subprocess.check_output(["sysctl", "hw.optional.arm.FEAT_SME"]).decode()
            SME_presence = True if SME_presence.split(": ")[1].strip() == "1" else False

            SME2_presence = subprocess.check_output(["sysctl", "hw.optional.arm.FEAT_SME2"]).decode()
            SME2_presence = True if SME2_presence.split(": ")[1].strip() == "1" else False


            if SME_presence or SME2_presence:
                cpu_info.arch_version = "9"
            else:
                cpu_info.arch_version = "8"
        except Exception as e:
            cpu_info.status = PartialStatus()

    return cpu_info
