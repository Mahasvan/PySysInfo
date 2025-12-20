from src.pysysinfo.dumps.mac.ioreg import *
from CoreFoundation import kCFAllocatorDefault

from src.pysysinfo.models.disk_models import StorageInfo, DiskInfo
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus


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

            # print(device)


            product = device.get("Device Characteristics")
            protocol = device.get("Protocol Characteristics")

            if not (product and protocol):
                continue

            # Name of the storage device.
            name = product.get("Product Name")

            # Name of vendor
            vendor = product.get("Vendor Name")
            if not vendor and "apple" in name.lower():
                vendor = "Apple"

            # Type of storage device (SSD, HDD, etc.)
            _type = product.get("Medium Type")
            if not _type: _type = "Unknown"

            # Type of connector (SATA, USB, SCSI, etc.)
            ct_type = protocol.get("Physical Interconnect")
            if not ct_type: ct_type = "Unknown"

            # Whether this device is internal or external.
            location = protocol.get("Physical Interconnect Location").strip()
            if not location: location = "Unknown"

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
            storage_info.status = PartialStatus()

    return storage_info