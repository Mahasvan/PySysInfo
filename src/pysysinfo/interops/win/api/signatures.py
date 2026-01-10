import ctypes
from ctypes import wintypes
from importlib import resources
from pysysinfo.interops.win.api.structs import *

user32 = ctypes.WinDLL("user32", use_last_error=True)
setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

# --------------------
# gpu_helper.dll
# --------------------
with resources.path("pysysinfo.interops.win.dll", "gpu_helper.dll") as dll_path:
    gpu_helper = ctypes.WinDLL(str(dll_path), use_last_error=True)

gpu_helper.GetGPUForDisplay.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
gpu_helper.GetGPUForDisplay.restype = ctypes.c_uint32
GetGPUForDisplay = gpu_helper.GetGPUForDisplay

gpu_helper.GetWmiInfo.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int,
]
gpu_helper.GetWmiInfo.restype = None
GetWmiInfo = gpu_helper.GetWmiInfo

# --------------------
# User32.dll
# --------------------

# BOOL EnumDisplayMonitors(HDC hdc, LPCRECT lprcClip, MONITORENUMPROC lpfnEnum, LPARAM dwData)
user32.EnumDisplayMonitors.argtypes = [
    wintypes.HDC,
    ctypes.c_void_p,
    MONITORENUMPROC,
    wintypes.LPARAM,
]
user32.EnumDisplayMonitors.restype = wintypes.BOOL
EnumDisplayMonitors = user32.EnumDisplayMonitors

# BOOL GetMonitorInfoA(HMONITOR hMonitor, LPMONITORINFO lpmi)
user32.GetMonitorInfoA.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXA)]
user32.GetMonitorInfoA.restype = wintypes.BOOL
GetMonitorInfoA = user32.GetMonitorInfoA

# BOOL EnumDisplaySettingsA(LPCSTR lpszDeviceName, DWORD iModeNum, DEVMODEA *lpDevMode)
user32.EnumDisplaySettingsA.argtypes = [
    wintypes.LPCSTR,
    wintypes.DWORD,
    ctypes.POINTER(DEVMODEA),
]
user32.EnumDisplaySettingsA.restype = wintypes.BOOL
EnumDisplaySettingsA = user32.EnumDisplaySettingsA

# BOOL EnumDisplayDevicesA(LPCSTR lpDevice, DWORD iDevNum, PDISPLAY_DEVICEA lpDisplayDevice, DWORD dwFlags)
user32.EnumDisplayDevicesA.argtypes = [
    wintypes.LPCSTR,
    wintypes.DWORD,
    ctypes.POINTER(DISPLAY_DEVICEA),
    wintypes.DWORD,
]
user32.EnumDisplayDevicesA.restype = wintypes.BOOL
EnumDisplayDevicesA = user32.EnumDisplayDevicesA

# --------------------
# Setupapi.dll
# --------------------

# HDEVINFO SetupDiGetClassDevsA(const GUID *ClassGuid, PCSTR Enumerator, HWND hwndParent, DWORD Flags)
setupapi.SetupDiGetClassDevsA.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.LPCSTR,
    wintypes.HWND,
    wintypes.DWORD,
]
setupapi.SetupDiGetClassDevsA.restype = wintypes.HANDLE
SetupDiGetClassDevsA = setupapi.SetupDiGetClassDevsA

# BOOL SetupDiEnumDeviceInfo(HDEVINFO DeviceInfoSet, DWORD MemberIndex, PSP_DEVINFO_DATA DeviceInfoData)
setupapi.SetupDiEnumDeviceInfo.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVINFO_DATA),
]
setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL
SetupDiEnumDeviceInfo = setupapi.SetupDiEnumDeviceInfo

# BOOL SetupDiEnumDeviceInterfaces(HDEVINFO DeviceInfoSet, PSP_DEVINFO_DATA DeviceInfoData, const GUID *InterfaceClassGuid, DWORD MemberIndex, PSP_DEVICE_INTERFACE_DATA DeviceInterfaceData)
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
]
setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
SetupDiEnumDeviceInterfaces = setupapi.SetupDiEnumDeviceInterfaces

# BOOL SetupDiGetDeviceInterfaceDetailA(HDEVINFO DeviceInfoSet, PSP_DEVICE_INTERFACE_DATA DeviceInterfaceData, PSP_DEVICE_INTERFACE_DETAIL_DATA_A DeviceInterfaceDetailData, DWORD DeviceInterfaceDetailDataSize, PDWORD RequiredSize, PSP_DEVINFO_DATA DeviceInfoData)
setupapi.SetupDiGetDeviceInterfaceDetailA.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(SP_DEVINFO_DATA),
]
setupapi.SetupDiGetDeviceInterfaceDetailA.restype = wintypes.BOOL
SetupDiGetDeviceInterfaceDetailA = setupapi.SetupDiGetDeviceInterfaceDetailA

# HKEY SetupDiOpenDevRegKey(HDEVINFO DeviceInfoSet, PSP_DEVINFO_DATA DeviceInfoData, DWORD Scope, DWORD HwProfile, DWORD KeyType, REGSAM samDesired)
setupapi.SetupDiOpenDevRegKey.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVINFO_DATA),
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
]
setupapi.SetupDiOpenDevRegKey.restype = wintypes.HKEY
SetupDiOpenDevRegKey = setupapi.SetupDiOpenDevRegKey

# BOOL SetupDiDestroyDeviceInfoList(HDEVINFO DeviceInfoSet)
setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]
setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
SetupDiDestroyDeviceInfoList = setupapi.SetupDiDestroyDeviceInfoList


# --------------------
# Advapi32.dll
# --------------------

# LSTATUS RegQueryValueExA(HKEY hKey, LPCSTR lpValueName, LPDWORD lpReserved, LPDWORD lpType, LPBYTE lpData, LPDWORD lpcbData)
advapi32.RegQueryValueExA.argtypes = [
    wintypes.HKEY,
    wintypes.LPCSTR,
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPBYTE,
    ctypes.POINTER(wintypes.DWORD),
]
advapi32.RegQueryValueExA.restype = wintypes.LONG
RegQueryValueExA = advapi32.RegQueryValueExA

# LSTATUS RegCloseKey(HKEY hKey)
advapi32.RegCloseKey.argtypes = [wintypes.HKEY]
advapi32.RegCloseKey.restype = wintypes.LONG
RegCloseKey = advapi32.RegCloseKey
