import os
import re
from typing import Optional

from pysysinfo.models.display_models import DisplayInfo, DisplayModuleInfo, ResolutionInfo


def _get_bits(data: bytes, start_bit: int, end_bit: int) -> int:
    # Get the bit values in an offset, given a bytes object.

    if start_bit < 0 or end_bit <= start_bit:
        raise ValueError("Invalid bit range")

    total_bits = len(data) * 8
    if end_bit > total_bits:
        raise ValueError("Bit range exceeds data length")

    # Convert bytes to integer
    value = int.from_bytes(data, byteorder="big")

    # Number of bits to extract
    length = end_bit - start_bit

    # Shift right to drop lower bits, then mask
    shift = total_bits - end_bit
    return (value >> shift) & ((1 << length) - 1)


BIT_DEPTH_ENUM = {
    1: 6,
    2: 8,
    3: 10,
    4: 12,
    5: 14,
    6: 16
}

INTERFACE_ENUM = {
    0: "Undefined",
    1: "DVI",
    2: "HDMI",  # Standard HDMI-A
    3: "HDMI (B)",
    4: "MDDI",
    5: "DisplayPort"
}

DESCRIPTOR_TAG_ENUM = {
    0xFF: "Serial Number",
    0xFE: "Alphanumeric Data String",
    0xFC: "Display Product Name",
}


def _parse_edid(edid_data: bytes):
    # todo: Parse EDID v1.2 and v1.3. This will work for v1.4, but need to verify on the older versions.
    module = DisplayModuleInfo()

    module.year = edid_data[0x11] + 1990

    manuf_bits = edid_data[0x15:0x17]
    manuf_string = ""
    # Manufacturer string is three 5-bit characters, and the MSB is ignored --> Total: 16 bits.
    for start in range(1, 12, 5):
        manuf_string += chr(_get_bits(manuf_bits, start, start + 5) + ord("A") - 1)

    module.manufacturer_code = manuf_string
    print("Manufacturer:", manuf_string)

    product_code = edid_data[0x0A:0x0C].hex().upper()
    print("product code:", product_code)

    id_serial_number = "0x" + edid_data[0x0C:0x10].hex().upper()

    input_type = edid_data[0x14]
    if input_type >> 7 == 1:  # MSB is 1 => Digital output
        module.resolution = ResolutionInfo()
        print("Digital Output")

        module.resolution.bit_depth = BIT_DEPTH_ENUM.get(_get_bits(input_type.to_bytes(1, byteorder="little"), 1, 5),
                                                         "Undefined")
        print("Bits per channel:", module.resolution.bit_depth)

        module.interface = INTERFACE_ENUM.get(input_type & 7, "Unknown")
        print("Interface:", module.interface)

    else:
        print("Analog Output")

    resolution = (0, 0, 0)  # Width, Height, Refresh Rate
    # We will use this tuple to find the max resolution and refresh rate, and update it in `module.resolution`.

    for block_start in range(0x36, 0x6d, 18):
        block = edid_data[block_start:block_start + 18]
        zeros = 0x00.to_bytes(1, byteorder='little') * 2
        if block[:2] == zeros:
            print("\nDetected Display Descriptor Block")
            tag = block[3]
            if tag not in DESCRIPTOR_TAG_ENUM:
                print("Unknown Tag:", tag)
            else:
                # Refer to DESCRIPTOR_TAG_ENUM for valid block type codes
                if tag == 0xFF:
                    # todo: test if this works
                    module.serial_number = block[5:].decode("ascii").strip()
                    print("Serial Number:", module.serial_number)
                if tag == 0xFC:
                    module.name = block[5:].decode("ascii").strip()
                    print("Product Name:", module.product_name)

            data = block[5:]
            data_str = ''.join([chr(byte) for byte in data])
            print("Data:", data_str.strip())

        else:
            print("\nTiming Descriptor Block:")
            if not module.resolution: continue

            pixel_clock_hz = (block[0] | (block[1] << 8)) * 10_000

            horiz = ((block[4] & 0xF0) << 4) | block[2]
            vert = ((block[7] & 0xF0) << 4) | block[5]

            h_blank = ((block[4] & 0x0F) << 8) | block[3]
            v_blank = ((block[7] & 0x0F) << 8) | block[6]
            refresh_rate = pixel_clock_hz / ((horiz + h_blank) * (vert + v_blank))
            print("Horizontal:", horiz)
            print("Vertical:", vert)
            print("Refresh Rate:", round(refresh_rate, 2))

            resolution = max(
                resolution,
                (horiz, vert, round(refresh_rate, 2)),
                key=lambda x: (x[0] * x[1], x[2])
            )

    if resolution != (0, 0, 0):
        module.resolution.width = resolution[0]
        module.resolution.height = resolution[1]
        module.resolution.refresh_rate = resolution[2]

    print("\nRaw EDID:")
    for byte in edid_data:
        print(f"{byte:02X}", end=" ")

    return module


def _fetch_individual_monitor_info(device_path: str, parent_device_path: str) -> Optional[DisplayModuleInfo]:
    path = os.path.join(device_path, "edid")
    if not os.path.exists(path): return None
    # todo: populate parent graphics card info
    with open(path, "rb") as f:
        edid_data = f.read()
    if len(edid_data) == 0: return None
    return _parse_edid(edid_data)


def fetch_display_info():
    display_info = DisplayInfo()
    pattern = re.compile(r"^card\d+$")
    root_path = "/sys/class/drm"
    parent_devices = os.listdir(root_path)
    parent_devices = [os.path.join(root_path, device) for device in parent_devices if pattern.match(device)]

    for parent_path in parent_devices:
        children = [x for x in os.listdir(parent_path) if x.startswith("card")]
        for child in children:
            response = _fetch_individual_monitor_info(os.path.join(parent_path, child), parent_path)
            if response:
                display_info.modules.append(response)

    return display_info
