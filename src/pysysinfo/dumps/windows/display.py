import ctypes
from importlib import resources
import os
from ctypes import wintypes
import struct
from typing import List, Optional

from pysysinfo.dumps.windows.win_enum import DISPLAY_CON_TYPE
from pysysinfo.interops.win.api.constants import *
from pysysinfo.interops.win.api.structs import *
from pysysinfo.interops.win.api.signatures import *
from pysysinfo.models.display_models import DisplayInfo, DisplayModuleInfo
from pysysinfo.models.status_models import Status, StatusType

# ------------------------------
# Utility functions
# ------------------------------


def parse_connector_info(connector_info: dict) -> Optional[dict]:
    """
    Parses the connector info string into a dictionary.
    The connector info string is in the format of:
       "DisplayID=\\\\.\\DISPLAYx|DisplayPath=\\\\?\\DISPLAY#<MANUF_CODE><PROD_CODE>#...|ConnectorType=int"
    """

    result = {}

    try:
        devices = connector_info.split("\n")

        for device in devices:
            parts = device.split("|")
            masterKey = None

            for part in parts:
                key, value = part.split("=")

                if key == "DisplayID":
                    result[value] = {}
                    masterKey = value

                else:
                    result[masterKey][key] = value
    except Exception as e:
        return None

    return result


def get_aspect_ratios(width: int, height: int) -> tuple[str, str, Optional[str]]:
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
        return (None, None, None)

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
    else:
        friendly = None

    # If display is in portrait mode, flip the ratio
    if width < height:
        parts = friendly.split(":")
        friendly = f"{parts[1]}:{parts[0]}"

    return (ratio, real, friendly)


# ------------------------------
# EDID parsing
# ------------------------------


def uniquely_identify_display_path(display_path: str) -> str:
    """
    Returns the serial number of the display from its display path string.

    The display path is in the format of: "\\?\DISPLAY#<MANUF_CODE><PROD_CODE>#..."
    """
    return get_edid_by_hwid(display_path).get("serial", None)


def parse_edid(edid: bytes):
    if len(edid) < 128:
        return None

    vendor = struct.unpack(">H", edid[8:10])[0]
    product = struct.unpack("<H", edid[10:12])[0]
    serial = None

    for i in range(3):
        descriptor = edid[0x48 + (i * 18) : 0x48 + ((i + 1) * 18)]
        if descriptor[0:4] == b"\x00\x00\x00\xff":  # Display Descriptor Header - Serial Number
            serial_raw = descriptor[5:18].split(b"\x0a")[0]

            try:
                serial_str = serial_raw.decode(errors="ignore").strip()
                if len(serial_str) > 0:
                    serial = serial_str
            except Exception:
                pass

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


def find_monitor_gpu(device_name) -> tuple[str, int]:
    out_buffer = ctypes.create_string_buffer(256)
    encoded_name = device_name.encode("utf-8")

    res = GetGPUForDisplay(encoded_name, out_buffer, 256)
    result = (None, res)

    if res != STATUS_OK:
        return result

    val = out_buffer.value.decode("utf-8")

    if val and len(val) > 0:
        result = (val, res)

    return result


# ------------------------------
# Fetch EDID from registry for
# specific display device
# by its HardwareID
#
# i.e. "MONITOR\AG326UD\{...}"
# ------------------------------


def get_edid_by_hwid(hwid: str):
    if not hwid or len(hwid) == 0:
        return None

    hdev = SetupDiGetClassDevsA(
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

        if not SetupDiEnumDeviceInterfaces(
            hdev,
            None,
            ctypes.byref(GUID_DEVINTERFACE_MONITOR),
            iface_index,
            ctypes.byref(iface_data),
        ):
            break

        req_size = wintypes.DWORD(0)
        SetupDiGetDeviceInterfaceDetailA(
            hdev, ctypes.byref(iface_data), None, 0, ctypes.byref(req_size), None
        )

        if req_size.value > 0:
            cb_size = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6

            buf = ctypes.create_string_buffer(req_size.value)
            struct.pack_into("I", buf, 0, cb_size)

            dev_data = SP_DEVINFO_DATA()
            dev_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

            if SetupDiGetDeviceInterfaceDetailA(
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
                    hkey = SetupDiOpenDevRegKey(
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
                            RegQueryValueExA(
                                hkey, b"EDID", None, None, None, ctypes.byref(edid_size)
                            )
                            == 0
                        ):
                            edid_buf = (ctypes.c_ubyte * edid_size.value)()
                            if (
                                RegQueryValueExA(
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

                        RegCloseKey(hkey)
                        if parsed_edid:
                            break

        iface_index += 1

    SetupDiDestroyDeviceInfoList(hdev)
    return parsed_edid


# ------------------------------
# Monitor enumeration callback
# ------------------------------


def monitor_enum_proc(hmonitor, hdc, rect, lparam):
    ptr = ctypes.cast(lparam, ctypes.POINTER(ctypes.py_object))
    monitor_list: DisplayInfo = ptr.contents.value

    mi = MONITORINFOEXA()
    mi.cbSize = ctypes.sizeof(mi)
    GetMonitorInfoA(hmonitor, ctypes.byref(mi))
    devid = mi.szDevice.decode()

    if not devid:
        monitor_list.status = Status(type=StatusType.PARTIAL)
        monitor_list.status.messages.append(
            f"Failed to fetch Display device information, DeviceID is empty!"
        )

        return True  # Continue enumeration

    dm = DEVMODEA()
    dm.dmSize = ctypes.sizeof(dm)
    EnumDisplaySettingsA(mi.szDevice, ENUM_CURRENT_SETTINGS, ctypes.byref(dm))

    dd = DISPLAY_DEVICEA(cb=ctypes.sizeof(DISPLAY_DEVICEA))
    EnumDisplayDevicesA(mi.szDevice, 0, ctypes.byref(dd), 0)
    target_pnp_id = dd.DeviceID.decode()

    connector_info = getattr(monitor_list, "_connectorInfo", None)
    connection_type = None
    device_path = None

    if not target_pnp_id or not len(target_pnp_id):
        monitor_list.status = Status(type=StatusType.PARTIAL)
        monitor_list.status.messages.append(
            f"Failed to fetch Display device information, PNPDeviceID is empty!"
        )

        return True  # Continue enumeration

    p_gpu, res_code = find_monitor_gpu(devid)

    # It is way more accurate to fetch EDID by the display path
    # rather than by the PNPDeviceID, as multiple displays
    # may be identical
    if connector_info:
        connector_info = connector_info.get(devid, None)
        connection_type = DISPLAY_CON_TYPE.get(
            int(connector_info.get("OutputTechnology", -2)), None
        )
        device_path = connector_info.get("DisplayPath", None)
        edid = get_edid_by_hwid(connector_info.get("DisplayPath", None))

    # Fallback to PNPDeviceID if no display path found
    else:
        edid = get_edid_by_hwid(target_pnp_id.split("\\")[1]) if target_pnp_id else None

    orientation = dm.dmDisplayOrientation

    monitor_info = DisplayModuleInfo()
    monitor_info.name = edid.get("name", None) if edid else None
    monitor_info.parent_gpu = p_gpu if res_code == STATUS_OK else None
    monitor_info.device_id = devid
    monitor_info.hardware_id = target_pnp_id
    monitor_info.device_path = device_path
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

    monitor_info.connection_type = connection_type
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

    return True  # Continue enumeration


def fetch_display_info_internal() -> DisplayInfo:
    monitors = DisplayInfo()
    monitors_ptr = ctypes.py_object(monitors)

    connectorInfo = ctypes.create_string_buffer(4096)
    res_code = GetDisplayPathInfo(connectorInfo, 4096)

    if res_code != STATUS_OK:
        monitors.status.type = StatusType.PARTIAL
        monitors.status.messages.append(
            f"Failed to fetch Display connector information, error code: {res_code}"
        )
    else:
        monitors._connectorInfo = parse_connector_info(
            connectorInfo.value.decode("utf-8", errors="ignore").strip()
        )

    enum_proc = MONITORENUMPROC(monitor_enum_proc)
    EnumDisplayMonitors(0, 0, enum_proc, ctypes.addressof(monitors_ptr))

    if len(monitors.modules) == 0:
        monitors.status.type = StatusType.FAILED

    return monitors
