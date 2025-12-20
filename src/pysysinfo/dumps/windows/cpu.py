import time
from typing import List
import ctypes

from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.status_models import PartialStatus, FailedStatus
from src.pysysinfo.dumps.windows.cpuid import CPUID

import winreg
import os

"""
Thanks to workhorsy and flababah for their implementations, on which my implementation is based.
References: 
- https://github.com/flababah/cpuid.py
- https://github.com/workhorsy/py-cpuinfo/blob/master/cpuinfo/cpuinfo.py
"""

def is_set(cpu, leaf, subleaf, reg_idx, bit):
    regs = cpu(leaf, subleaf)

    return bool((1 << bit) & regs[reg_idx])

def get_features(cpu: CPUID) -> List[str]:
    SSE = ["SSE", "SSE2", "SSE3", "SSE4.1", "SSE4.2"]
    """
    The SSE feature flags are located in the ECX and EDX registers.
    Each bit in those registers corresponds to a specific feature, and we check if that bit is set or unset.
    https://en.wikipedia.org/wiki/CPUID#EAX=7,_ECX=0:_Extended_Features
    """
    SSE_OP = [
        (1, 0, 3, 25),  # SSE
        (1, 0, 3, 26),  # SSE2
        (1, 0, 2, 0),   # SSE3
        (1, 0, 2, 19),  # SSE4.1
        (1, 0, 2, 20),  # SSE4.2
    ]
    SSSE3 = is_set(cpu, 1, 0, 2, 9)
    
    features = []
    for i in range(len(SSE)):
        if is_set(cpu, *SSE_OP[i]):
            features.append(SSE[i])
    if SSSE3:
        features.append("SSSE3")

    return features

def parse_registry():
    """
    We can get the CPU model name and vendor from the Windows Registry from the following path:
    "HKEY_LOCAL_MACHINE -> HARDWARE -> DESCRIPTION -> System -> CentralProcessor -> 0"
    """
    key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    model_key = "ProcessorNameString"
    vendor_key = "VendorIdentifier"
    
    model_name = ""
    vendor = ""

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        key_path,
        0,
        winreg.KEY_READ
    ) as key:
        model_name, _ = winreg.QueryValueEx(key, model_key)
        vendor, _ = winreg.QueryValueEx(key, vendor_key)
        return model_name, vendor

def get_core_count() -> int:
    """
    Uses the GetLogicalProcessorInformation function in the Win32 API to get the number of physical cores.
    https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformation
    """
    
    """
    typedef struct _SYSTEM_LOGICAL_PROCESSOR_INFORMATION {
        ULONG_PTR ProcessorMask;
        LOGICAL_PROCESSOR_RELATIONSHIP Relationship;
        union {
            struct {
                BYTE Flags;
            } ProcessorCore;
            struct {
                DWORD NodeNumber;
            } NumaNode;
            CACHE_DESCRIPTOR Cache;
            ULONGLONG Reserved[2];
        };
    } SYSTEM_LOGICAL_PROCESSOR_INFORMATION;
    
    ProcessorMask - Pointer - 8 bytes
    Relationship - DWORD - 4 bytes
    Padding - 4 byt
    Union - must be large enough to hold the largest member - 16 bytes
    Total size = 8 + 4 + 4 + 16 = 32 bytes
    """

    class SYSTEM_LOGICAL_PROCESSOR_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("ProcessorMask", ctypes.c_size_t),
            ("Relationship", ctypes.c_int),
            ("Reserved", ctypes.c_byte * 20),
        ]

    RelationProcessorCore = 0

    buffer_size = ctypes.c_ulong(0)
    ctypes.windll.kernel32.GetLogicalProcessorInformation(None, ctypes.byref(buffer_size))

    count = buffer_size.value // ctypes.sizeof(SYSTEM_LOGICAL_PROCESSOR_INFORMATION)
    buffer = (SYSTEM_LOGICAL_PROCESSOR_INFORMATION * count)()

    ctypes.windll.kernel32.GetLogicalProcessorInformation(
        buffer,
        ctypes.byref(buffer_size)
    )

    physical_cores = sum(
        1 for info in buffer if info.Relationship == RelationProcessorCore
    )
    
    return physical_cores

def fetch_cpu_info(wmi_instance) -> CPUInfo:
    cpu_info = CPUInfo()
    cpuid = CPUID()

    model_name, vendor = parse_registry()
    cpu_info.model_name = model_name.strip()
    cpu_info.vendor = "AMD" if "amd" in vendor.lower() else "Intel" if "intel" in vendor.lower() else vendor.strip()
    
    features = get_features(cpuid)
    cpu_info.sse_flags = features
    
    """
    The CPU Architecture is exposed as an environment variable on Windows systems.
    https://www.tenforums.com/tutorials/176966-how-check-if-processor-32-bit-64-bit-arm-windows-10-a.html
    
    Possible outputs:
    - x86 -> x86 32-bit
    - AMD64 -> x86 64-bit
    - ARM64 -> ARM 64-bit
    
    We account for "x86_64" and "i386" as well, just in case.
    """
    architecture = os.environ.get("PROCESSOR_ARCHITECTURE", "").lower()
    if "amd64" in architecture or "x86_64" in architecture:
        cpu_info.architecture = "x86"
        cpu_info.bitness = 64
    elif "x86" in architecture or "i386" in architecture:
        cpu_info.architecture = "x86"
        cpu_info.bitness = 32
    elif "arm64" in architecture:
        cpu_info.architecture = "ARM"
        cpu_info.bitness = 64
    else:
        cpu_info.status = PartialStatus()
    
    cpu_info.cores = get_core_count()
    if not cpu_info.cores:
        cpu_info.status = PartialStatus()
    cpu_info.threads = os.cpu_count()
    if not cpu_info.threads:
        cpu_info.status = PartialStatus()

    return cpu_info
