from src.pysysinfo.dumps.mac.ioreg import *
from CoreFoundation import kCFAllocatorDefault

from src.pysysinfo.models.storage_models import StorageInfo, DiskInfo
from src.pysysinfo.models.status_models import PartialStatus


STORAGE_MAP = {
    "Solid State": "Solid State Drive (SSD)",
    "Rotational": "Hard Disk Drive (HDD)",
}


def fetch_storage_info() -> StorageInfo:
    storage_info = StorageInfo()
    # todo: fetch storage capacity
    device = {"IOProviderClass": "IOBlockStorageDevice"}

    interfaces = ioiterator_to_list(
        IOServiceGetMatchingServices(kIOMasterPortDefault, device, None)[1]
    )

    for i in interfaces:
        try:
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

            disk = DiskInfo()
            disk.model = name
            disk.location = location
            disk.type = _type
            disk.vendor_name = vendor

            storage_info.disks.append(disk)
        except Exception as e:
            print(e)
            storage_info.status = PartialStatus(messages=storage_info.status.messages)
            storage_info.status.messages.append("Error while enumerating storage: " + str(e))

    return storage_info