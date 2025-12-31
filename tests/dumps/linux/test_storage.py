import builtins
import os
from unittest.mock import MagicMock

from pysysinfo.dumps.linux.storage import fetch_storage_info
from pysysinfo.models.status_models import FailedStatus, PartialStatus, SuccessStatus


class TestLinuxStorage:

    def test_fetch_storage_info_no_sys_block(self, monkeypatch):
        monkeypatch.setattr(os.path, "isdir", lambda x: False)

        storage_info = fetch_storage_info()

        assert isinstance(storage_info.status, FailedStatus)
        assert "does not exist" in storage_info.status.messages[0]

    def test_fetch_storage_info_nvme_success(self, monkeypatch):
        monkeypatch.setattr(os.path, "isdir", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["nvme0n1", "loop0"])

        def mock_open(path, mode="r"):
            mock_file = MagicMock()
            content = ""
            if "nvme0n1/device/model" in path:
                content = "Samsung SSD 970 EVO Plus 1TB"
            elif "nvme0n1/queue/rotational" in path:
                content = "0"
            elif "nvme0n1/removable" in path:
                content = "0"
            elif "nvme0n1/device/device/device" in path:
                content = "0xa808"
            elif "nvme0n1/device/device/vendor" in path:
                content = "0x144d"
            elif "nvme0n1/size" in path:
                content = "1953525168"  # 1TB in 512-byte blocks

            mock_file.read.return_value = content
            mock_file.__enter__.return_value = mock_file
            return mock_file

        monkeypatch.setattr(builtins, "open", mock_open)

        storage_info = fetch_storage_info()

        assert isinstance(storage_info.status, SuccessStatus)
        assert len(storage_info.disks) == 1
        disk = storage_info.disks[0]
        assert disk.model == "Samsung SSD 970 EVO Plus 1TB"
        assert disk.type == "Non-Volatile Memory Express (NVMe)"
        assert disk.location == "Internal"
        assert disk.connector == "PCIe"
        assert disk.vendor_id == "0x144d"
        assert disk.device_id == "0xa808"
        # 1953525168 * 512 / 1024 / 1024 = 953869.7109375 MB -> 953869 MB
        assert disk.size is not None
        assert disk.size.capacity == 953869

    def test_fetch_storage_info_sd_success(self, monkeypatch):
        monkeypatch.setattr(os.path, "isdir", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["sda"])

        def mock_open(path, mode="r"):
            mock_file = MagicMock()
            content = ""
            if "sda/device/model" in path:
                content = "WDC WD10EZEX-08W"
            elif "sda/queue/rotational" in path:
                content = "1"
            elif "sda/removable" in path:
                content = "0"
            elif "sda/device/vendor" in path:
                content = "ATA"
            elif "sda/size" in path:
                content = "1953525168"

            mock_file.read.return_value = content
            mock_file.__enter__.return_value = mock_file
            return mock_file

        monkeypatch.setattr(builtins, "open", mock_open)

        storage_info = fetch_storage_info()

        assert isinstance(storage_info.status, SuccessStatus)
        assert len(storage_info.disks) == 1
        disk = storage_info.disks[0]
        assert disk.model == "WDC WD10EZEX-08W"
        assert disk.type == "Hard Disk Drive (HDD)"
        assert disk.location == "Internal"
        assert disk.connector == "SCSI"
        assert disk.vendor_id == "ATA"
        assert disk.size is not None
        assert disk.size.capacity == 953869

    def test_fetch_storage_info_partial_failure(self, monkeypatch):
        monkeypatch.setattr(os.path, "isdir", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["sda"])

        def mock_open(path, mode="r"):
            mock_file = MagicMock()
            content = ""
            if "sda/device/model" in path:
                content = ""  # Empty model
            elif "sda/queue/rotational" in path:
                content = "1"
            elif "sda/removable" in path:
                content = "0"
            elif "sda/device/vendor" in path:
                content = "ATA"
            elif "sda/size" in path:
                content = "1000"

            mock_file.read.return_value = content
            mock_file.__enter__.return_value = mock_file
            return mock_file

        monkeypatch.setattr(builtins, "open", mock_open)

        storage_info = fetch_storage_info()

        assert isinstance(storage_info.status, PartialStatus)
        assert "Disk Model could not be found" in storage_info.status.messages
        assert len(storage_info.disks) == 1

    def test_fetch_storage_info_exception(self, monkeypatch):
        monkeypatch.setattr(os.path, "isdir", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["sda"])

        def mock_open(path, mode="r"):
            raise PermissionError("Access denied")

        monkeypatch.setattr(builtins, "open", mock_open)

        storage_info = fetch_storage_info()

        assert isinstance(storage_info.status, PartialStatus)
        assert any("Disk Info: Access denied" in msg for msg in storage_info.status.messages)
        assert len(storage_info.disks) == 1
