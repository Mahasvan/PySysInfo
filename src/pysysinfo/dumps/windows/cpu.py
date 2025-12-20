from typing import List
import ctypes
from ctypes import wintypes

from src.pysysinfo.models.cpu_models import CPUInfo
from src.pysysinfo.models.status_models import PartialStatus

import winreg
import os

"""
Thanks to workhorsy and flababah for their implementations, on which my implementation is based.
References: 
- https://github.com/flababah/cpuid.py
- https://github.com/workhorsy/py-cpuinfo/blob/master/cpuinfo/cpuinfo.py
"""

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.IsProcessorFeaturePresent.argtypes = [wintypes.DWORD]
kernel32.IsProcessorFeaturePresent.restype = wintypes.BOOL

def is_processor_feature_present(feature_id: int) -> bool:
    """
    Checks whether the specified processor feature is present.

    :param feature_id: One of the PF_* constants defined by Windows.
    :return: True if the feature is present, False otherwise.
    """
    return bool(kernel32.IsProcessorFeaturePresent(feature_id))

def get_arm_version() -> str:
    """
    We use instructions that were introduced in different ARM versions to determine the ARM version.
    
    ARMv9
    - SVE2 - FEAT_SSVE_FP8DOT2 (78), FEAT_SSVE_FP8DOT4 (79), and FEAT_SSVE_FP8FMA (80)
    
    ARMv8
    - Full AArch64 Instructions - FEAT_SME_FA64 (88)
    
    Otherwise
    - we can assume it's ARMv7 or lower.
    """
    if any([is_processor_feature_present(i) for i in [78,79,80]]):
        return "9"
    elif is_processor_feature_present(88):
        return "8"
    else:
        return "Unknown"

def get_features() -> List[str]:
    """
    We use the Win32 API function IsProcessorFeaturePresent to check for SSE features.
    https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-isprocessorfeaturepresent
    
    Feature IDs:
    - SSE - 6
    - SSE2 - 10
    - SSE3 - 13
    - SSSE3 - 36
    - SSE4.1 - 37
    - SSE4.2 - 38
    """
    SSE = ["SSE", "SSE2", "SSE3", "SSE4.1", "SSE4.2", "SSSE3"]
    FEATURE_IDs = [6,10,13,37,38,36]
    
    
    features = []
    for i in range(len(SSE)):
        if is_processor_feature_present(FEATURE_IDs[i]):
            features.append(SSE[i])
    
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

def fetch_cpu_info() -> CPUInfo:
    cpu_info = CPUInfo()

    model_name, vendor = parse_registry()
    cpu_info.model_name = model_name.strip()
    cpu_info.vendor = "AMD" if "amd" in vendor.lower() else "Intel" if "intel" in vendor.lower() else vendor.strip()
    
    features = get_features()
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
