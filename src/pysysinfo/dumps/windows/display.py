import ctypes
from importlib import resources
import os
from ctypes import wintypes
import struct
from typing import List, Optional

from pysysinfo.models.display_models import DisplayInfo, DisplayModuleInfo

# ------------------------------
# Win32 constants & structures
# ------------------------------

WIN32_LEAN_AND_MEAN = True

ENUM_CURRENT_SETTINGS = -1
DIGCF_PRESENT = 0x00000002
DICS_FLAG_GLOBAL = 0x00000001
DIREG_DEV = 0x00000001
KEY_READ = 0x20019
REG_BINARY = 3

# Orientation values
DMDO_DEFAULT = 0  # Landscape
DMDO_90 = 1  # Portrait
DMDO_180 = 2  # Landscape (flipped)
DMDO_270 = 3  # Portrait (flipped)

user32 = ctypes.WinDLL("user32", use_last_error=True)
setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
ole32 = ctypes.WinDLL("ole32", use_last_error=True)

with resources.path("pysysinfo.interops.win.dll", "gpu_helper.dll") as dll_path:
    gpu_helper = ctypes.CDLL(str(dll_path))

gpu_helper.GetGPUForDisplay.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
gpu_helper.GetGPUForDisplay.restype = None

# ------------------------------
# GUID helper
# ------------------------------


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


GUID_DEVCLASS_MONITOR = GUID(
    0x4D36E96E,
    0xE325,
    0x11CE,
    (ctypes.c_ubyte * 8)(0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18),
)

GUID_DEVINTERFACE_MONITOR = GUID(
    0xE6F07B5F,
    0xEE97,
    0x4A90,
    (ctypes.c_ubyte * 8)(0xB0, 0x76, 0x33, 0xF5, 0x7B, 0xF4, 0xEA, 0xA7),
)

# ------------------------------
# Structures
# ------------------------------


class MONITORINFOEXA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_char * 32),
    ]


class DEVMODEA(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_char * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPositionX", wintypes.LONG),
        ("dmPositionY", wintypes.LONG),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", ctypes.c_char * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
    ]


class DISPLAY_DEVICEA(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", ctypes.c_char * 32),
        ("DeviceString", ctypes.c_char * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", ctypes.c_char * 128),
        ("DeviceKey", ctypes.c_char * 128),
    ]


class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", wintypes.LPVOID),
    ]


class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.c_void_p),
    ]


class SP_INTERFACE_DEVICE_DETAIL_DATA_A(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("DevicePath", ctypes.c_char * 1),
    ]


MONITORENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(wintypes.RECT),
    wintypes.LPARAM,
)

user32.EnumDisplayMonitors.argtypes = [
    wintypes.HDC,
    ctypes.c_void_p,
    MONITORENUMPROC,
    wintypes.LPARAM,
]
user32.EnumDisplayMonitors.restype = wintypes.BOOL

setupapi.SetupDiGetClassDevsA.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.LPCSTR,
    wintypes.HWND,
    wintypes.DWORD,
]
setupapi.SetupDiGetClassDevsA.restype = wintypes.HANDLE

setupapi.SetupDiEnumDeviceInfo.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVINFO_DATA),
]
setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL

setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
]
setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL

setupapi.SetupDiGetDeviceInterfaceDetailA.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(SP_DEVINFO_DATA),
]
setupapi.SetupDiGetDeviceInterfaceDetailA.restype = wintypes.BOOL

setupapi.SetupDiOpenDevRegKey.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVINFO_DATA),
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
]
setupapi.SetupDiOpenDevRegKey.restype = wintypes.HKEY

setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]
setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

advapi32.RegQueryValueExA.argtypes = [
    wintypes.HKEY,
    wintypes.LPCSTR,
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPBYTE,
    ctypes.POINTER(wintypes.DWORD),
]
advapi32.RegQueryValueExA.restype = wintypes.LONG

advapi32.RegCloseKey.argtypes = [wintypes.HKEY]
advapi32.RegCloseKey.restype = wintypes.LONG

# ------------------------------
# Utility functions
# ------------------------------


def get_aspect_ratios(width: int, height: int) -> tuple[str, str]:
    """
    Obtains the "friendly" and "real" representation of
    the aspect ratio's given width and height.

    I.e., 3440x1440 -> "21:9" & "43:18"

    Falls back to the mathematical form if unable
    to compute a friendly ratio.
    """

    def gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    if width == 0 or height == 0:
        return None

    long_side = max(width, height)
    short_side = min(width, height)
    ratio = long_side / short_side

    divisor = gcd(width, height)
    real = friendly = f"{width // divisor}:{height // divisor}"

    if 3.5 <= ratio <= 3.6:
        friendly = "32:9"
    elif 2.3 <= ratio <= 2.4:
        friendly = "21:9"
    elif 1.7 <= ratio <= 1.8:
        friendly = "16:9"
    elif 1.55 <= ratio <= 1.65:
        friendly = "16:10"
    elif 1.3 <= ratio <= 1.35:
        friendly = "4:3"

    # If display is in portrait mode, flip the ratio
    if width < height:
        parts = friendly.split(":")
        friendly = f"{parts[1]}:{parts[0]}"

    return (ratio, real, friendly)


# ------------------------------
# EDID parsing
# ------------------------------


def parse_edid(edid: bytes):
    if len(edid) < 128:
        return {}

    vendor = struct.unpack(">H", edid[8:10])[0]
    product = struct.unpack("<H", edid[10:12])[0]
    serial = struct.unpack("<I", edid[12:16])[0]

    char1 = chr(((vendor >> 10) & 0x1F) + 64)
    char2 = chr(((vendor >> 5) & 0x1F) + 64)
    char3 = chr((vendor & 0x1F) + 64)
    manufacturer_code = f"{char1}{char2}{char3}"

    width_cm = edid[21]
    height_cm = edid[22]

    diag_inch = 0.0
    if width_cm > 0 and height_cm > 0:
        diag_cm = (width_cm**2 + height_cm**2) ** 0.5
        diag_inch = round(diag_cm / 2.54)

    name = ""
    for i in range(4):
        off = 54 + i * 18
        if edid[off : off + 4] == b"\x00\x00\x00\xfc":
            raw = edid[off + 5 : off + 18].split(b"\x0a")[0]
            name = raw.decode(errors="ignore").strip()

    return {
        "manufacturer_code": manufacturer_code,
        "vendor_id": vendor,
        "product_id": product,
        "serial": serial,
        "name": name,
        "inches": diag_inch,
    }


def find_monitor_gpu(device_name) -> Optional[str]:
    out_buffer = ctypes.create_string_buffer(256)
    encoded_name = device_name.encode("utf-8")

    try:
        gpu_helper.GetGPUForDisplay(encoded_name, out_buffer, 256)

        return out_buffer.value.decode("utf-8")
    except Exception as e:
        print(f"Error calling DLL: {e}")


# ------------------------------
# Read EDID from registry for
# specific display device
# by its HardwareID
#
# i.e. "MONITOR\AG326UD\{...}"
# ------------------------------


def get_edid_by_hwid(hwid: str):
    DIGCF_PRESENT = 0x00000002
    DIGCF_DEVICEINTERFACE = 0x00000010
    DICS_FLAG_GLOBAL = 0x00000001
    DIREG_DEV = 0x00000001
    KEY_READ = 0x20019

    hdev = setupapi.SetupDiGetClassDevsA(
        ctypes.byref(GUID_DEVINTERFACE_MONITOR),
        None,
        None,
        DIGCF_PRESENT | DIGCF_DEVICEINTERFACE,
    )

    if hdev == -1:
        return None

    iface_index = 0
    parsed_edid = None

    while True:
        iface_data = SP_DEVICE_INTERFACE_DATA()
        iface_data.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)

        if not setupapi.SetupDiEnumDeviceInterfaces(
            hdev,
            None,
            ctypes.byref(GUID_DEVINTERFACE_MONITOR),
            iface_index,
            ctypes.byref(iface_data),
        ):
            break

        req_size = wintypes.DWORD(0)
        setupapi.SetupDiGetDeviceInterfaceDetailA(
            hdev, ctypes.byref(iface_data), None, 0, ctypes.byref(req_size), None
        )

        if req_size.value > 0:
            cb_size = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6

            buf = ctypes.create_string_buffer(req_size.value)
            struct.pack_into("I", buf, 0, cb_size)

            dev_data = SP_DEVINFO_DATA()
            dev_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

            if setupapi.SetupDiGetDeviceInterfaceDetailA(
                hdev,
                ctypes.byref(iface_data),
                buf,
                req_size,
                None,
                ctypes.byref(dev_data),
            ):
                path_offset = wintypes.DWORD
                raw_path = ctypes.string_at(
                    ctypes.addressof(buf) + ctypes.sizeof(path_offset)
                )
                device_path = raw_path.decode("ascii", errors="ignore").upper()

                if hwid.upper() in device_path:
                    hkey = setupapi.SetupDiOpenDevRegKey(
                        hdev,
                        ctypes.byref(dev_data),
                        DICS_FLAG_GLOBAL,
                        0,
                        DIREG_DEV,
                        KEY_READ,
                    )

                    if hkey != -1 and hkey != 0:
                        edid_size = wintypes.DWORD()

                        if (
                            advapi32.RegQueryValueExA(
                                hkey, b"EDID", None, None, None, ctypes.byref(edid_size)
                            )
                            == 0
                        ):
                            edid_buf = (ctypes.c_ubyte * edid_size.value)()
                            if (
                                advapi32.RegQueryValueExA(
                                    hkey,
                                    b"EDID",
                                    None,
                                    None,
                                    edid_buf,
                                    ctypes.byref(edid_size),
                                )
                                == 0
                            ):
                                parsed_edid = parse_edid(bytes(edid_buf))

                        advapi32.RegCloseKey(hkey)
                        if parsed_edid:
                            break

        iface_index += 1

    setupapi.SetupDiDestroyDeviceInfoList(hdev)
    return parsed_edid


# ------------------------------
# Monitor enumeration callback
# ------------------------------


def monitor_enum_proc(hmonitor, hdc, rect, lparam):
    ptr = ctypes.cast(lparam, ctypes.POINTER(ctypes.py_object))
    monitor_list = ptr.contents.value

    mi = MONITORINFOEXA()
    mi.cbSize = ctypes.sizeof(mi)
    user32.GetMonitorInfoA(hmonitor, ctypes.byref(mi))
    devid = mi.szDevice.decode()

    dm = DEVMODEA()
    dm.dmSize = ctypes.sizeof(dm)
    user32.EnumDisplaySettingsA(mi.szDevice, ENUM_CURRENT_SETTINGS, ctypes.byref(dm))

    dd = DISPLAY_DEVICEA(cb=ctypes.sizeof(DISPLAY_DEVICEA))
    user32.EnumDisplayDevicesA(mi.szDevice, 0, ctypes.byref(dd), 0)
    target_pnp_id = dd.DeviceID.decode()

    p_gpu = find_monitor_gpu(devid)
    edid = get_edid_by_hwid(target_pnp_id.split("\\")[1])

    orientation = dm.dmDisplayOrientation

    monitor_info = DisplayModuleInfo()
    monitor_info.name = edid.get("name", None) if edid else None
    monitor_info.parent_gpu = p_gpu
    monitor_info.device_id = devid
    monitor_info.hardware_id = target_pnp_id
    monitor_info.resolution.width = dm.dmPelsWidth
    monitor_info.resolution.height = dm.dmPelsHeight
    monitor_info.resolution.refresh_rate = dm.dmDisplayFrequency
    (
        monitor_info.resolution.aspect_ratio,
        monitor_info.resolution.aspect_ratio_real,
        monitor_info.resolution.aspect_ratio_friendly,
    ) = get_aspect_ratios(dm.dmPelsWidth, dm.dmPelsHeight)

    if orientation == DMDO_DEFAULT:
        monitor_info.orientation = "Landscape"
    elif orientation == DMDO_90:
        monitor_info.orientation = "Portrait"
    elif orientation == DMDO_180:
        monitor_info.orientation = "Landscape (flipped)"
    elif orientation == DMDO_270:
        monitor_info.orientation = "Portrait (flipped)"
    else:
        monitor_info.orientation = "Unknown"

    monitor_info.inches = edid.get("inches", None) if edid else None
    monitor_info.vendor_id = f"0x{edid['vendor_id']:04X}" if edid else None
    monitor_info.product_id = f"0x{edid['product_id']:04X}" if edid else None
    monitor_info.serial_number = (
        str(edid["serial"]) if edid and edid.get("serial") is not None else None
    )
    monitor_info.manufacturer_code = (
        edid.get("manufacturer_code", None) if edid else None
    )

    monitor_list.modules.append(monitor_info)

    return True


def fetch_display_info_internal() -> DisplayInfo:
    monitors = DisplayInfo()
    monitors_ptr = ctypes.py_object(monitors)

    enum_proc = MONITORENUMPROC(monitor_enum_proc)
    user32.EnumDisplayMonitors(0, 0, enum_proc, ctypes.addressof(monitors_ptr))

    return monitors
