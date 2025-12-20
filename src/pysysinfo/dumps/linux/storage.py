import os
from pyexpat.errors import messages

from src.pysysinfo.models.storage_models import StorageInfo, DiskInfo
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus
from src.pysysinfo.models.size_models import Megabyte


def fetch_storage_info() -> StorageInfo:
    storage_info = StorageInfo()

    # Storage Block Information is in /sys/block
    # todo: if /sys/subsystem exists, do not parse /sys/block
    # https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html#:~:text=Classification%20by%20subsystem

    if not os.path.isdir("/sys/block"):
        storage_info.status = FailedStatus("The /sys/block directory does not exist")
        return storage_info

    for folder in os.listdir("/sys/block"):
        disk = DiskInfo()

        path = f"/sys/block/{folder}"
        # todo: mmcblk detection e.g. eMMC storage
        try:
            if (not "nvme" in folder) and (not "sd" in folder):
                continue

            # Check properties of block device
            model = open(f"{path}/device/model", "r").read().strip()

            if model:
                disk.model = model
            else:
                storage_info.status = PartialStatus(messages=storage_info.status.messages)
                storage_info.status.messages.append("Disk Model could not be found")

            rotational = open(f"{path}/queue/rotational", "r").read().strip()
            removable = open(f"{path}/removable", "r").read().strip()

            # todo: USB block devices all report as HDDs?
            disk.type = (
                "Solid State Drive (SSD)"
                if rotational == "0"
                else "Hard Disk Drive (HDD)"
            )

            disk.location = "Internal" if removable == "0" else "External"

            if "nvme" in folder:
                disk.connector = "PCIe"
                disk.type = "Non-Volatile Memory Express (NVMe)"

                # Uses PCI vendor & device ids to get a vendor for the NVMe block device
                disk.device_id = open(f"{path}/device/device/device",
                                      "r").read().strip()
                disk.vendor_id = open(f"{path}/device/device/vendor",
                                      "r").read().strip()
            elif "sd" in folder:
                # todo: Choose correct connector type for block devices that use the SCSI subsystem
                disk.connector = "SCSI"
                disk.vendor_id = open(f"{path}/device/vendor", "r").read().strip()
            else:
                disk.connector = "Unknown"

            """
            Disk Size - Is the value in /sys/block/sda/size Multiplied by the Block Size
            In Linux, the block size is always considered as 512
            - https://github.com/torvalds/linux/blob/master/include/linux/types.h#L132
            """

            size = open(f"{path}/size", "r").read().strip()
            size_in_bytes = int(size) * 512
            disk.size = Megabyte(capacity=(size_in_bytes // 1024 ** 2))

        except Exception as e:
            storage_info.status = PartialStatus(messages=storage_info.status.messages)
            storage_info.status.messages.append("Disk Info: " + str(e))

        storage_info.disks.append(disk)

    return storage_info
