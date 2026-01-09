from ctypes import wintypes
import ctypes
from pysysinfo.interops.win.api.structs import GUID

# Win32 General Constants
ENUM_CURRENT_SETTINGS = -1
DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010
DICS_FLAG_GLOBAL = 0x00000001
DIREG_DEV = 0x00000001
KEY_READ = 0x20019
REG_BINARY = 3

# Registry access constants
DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010
DICS_FLAG_GLOBAL = 0x00000001
DIREG_DEV = 0x00000001
KEY_READ = 0x20019

# Orientation values
DMDO_DEFAULT = 0  # Landscape
DMDO_90 = 1  # Portrait
DMDO_180 = 2  # Landscape (flipped)
DMDO_270 = 3  # Portrait (flipped)

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
