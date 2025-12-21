from typing import Optional

from src.pysysinfo.dumps.mac.ioreg import *
from CoreFoundation import kCFAllocatorDefault

from src.pysysinfo.models.size_models import Megabyte
from src.pysysinfo.models.storage_models import StorageInfo, DiskInfo
from src.pysysinfo.models.status_models import PartialStatus

from ctypes import byref, create_string_buffer


STORAGE_MAP = {
    "Solid State": "Solid State Drive (SSD)",
    "Rotational": "Hard Disk Drive (HDD)",
}

def find_media(entry) -> dict:
    kr, iterator = IORegistryEntryGetChildIterator(
        entry,
        kIOServicePlane,
        None
    )

    if kr != 0 or not iterator:
        return {}

    for child in ioiterator_to_list(iterator):
        if IOObjectConformsTo(child, b"IOMedia"):
            kr, props = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    child, None, kCFAllocatorDefault, kNilOptions
                )
            )
            if kr != 0 or not props:
                continue

            if props.get("Whole"):
                return props

        # recurse
        result = find_media(child)
        if result:
            return result

    return {}


def fetch_storage_info() -> StorageInfo:
    storage_info = StorageInfo()
    device = {"IOProviderClass": "IOBlockStorageDevice"}

    interfaces = ioiterator_to_list(
        IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
    )

    for i in interfaces:
        try:
            # We first attempt to get the IOMedia entry for this IOBlockStorageDevice entry
            # by traversing down the tree
            try:
                media_info = find_media(i)
                if not media_info:
                    raise ValueError("Media Info is empty")
            except Exception as e:
                storage_info.status = PartialStatus(messages=storage_info.status.messages)
                storage_info.status.messages.append("Could not fetch media info: " + str(e))
                media_info = {}

            device = corefoundation_to_native(
                IORegistryEntryCreateCFProperties(
                    i, None, kCFAllocatorDefault, kNilOptions
                )
            )[1]

            product = device.get("Device Characteristics")
            protocol = device.get("Protocol Characteristics")

            if not (product and protocol):
                continue

            # Name of the storage device.
            name = product.get("Product Name")
            if name: name = name.strip()

            # Name of vendor
            vendor = product.get("Vendor Name")

            if vendor: vendor = vendor.strip()
            elif "apple" in name.lower():
                vendor = "Apple"

            # Type of storage device (SSD, HDD, etc.)
            _type = product.get("Medium Type")
            if _type:
                _type = _type.strip()
            else:
                _type = "Unknown"

            # Type of connector (SATA, USB, SCSI, etc.)
            ct_type = protocol.get("Physical Interconnect")
            if ct_type:
                ct_type = ct_type.strip()
            else:
                ct_type = "Unknown"

            # Whether this device is internal or external.
            location = protocol.get("Physical Interconnect Location", "")
            if location != "":
                location = location.strip()
            else:
                location: location = "Unknown"

            if ct_type.lower() == "pci-express":
                _type = "Non-Volatile Memory Express (NVMe)"
            else:
                _type = STORAGE_MAP.get(_type, _type)

            size = media_info.get("Size")

            disk = DiskInfo()
            disk.model = name
            disk.location = location
            disk.type = _type
            disk.manufacturer = vendor

            if size:
                disk.size = Megabyte(capacity=size // (1024*1024))

            storage_info.disks.append(disk)
        except Exception as e:
            print(e)
            storage_info.status = PartialStatus(messages=storage_info.status.messages)
            storage_info.status.messages.append("Error while enumerating storage: " + str(e))

    return storage_info