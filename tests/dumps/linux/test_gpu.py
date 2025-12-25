import os
import subprocess
import builtins
from unittest.mock import MagicMock, mock_open

from src.pysysinfo.dumps.linux.gpu import fetch_gpu_info
from src.pysysinfo.models.status_models import FailedStatus, PartialStatus, SuccessStatus
from src.pysysinfo.models.size_models import Megabyte

class TestLinuxGPU:

    def test_fetch_gpu_info_root_not_found(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: False)
        
        info = fetch_gpu_info()
        
        assert isinstance(info.status, FailedStatus)
        assert "not found" in info.status.messages[0]
        assert len(info.modules) == 0

    def test_fetch_gpu_info_success_generic(self, monkeypatch):
        # Mock os.path.exists
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        
        # Mock os.listdir
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:01:00.0", "0000:00:02.0"])
        
        # Mock open
        file_contents = {
            "class": "0x030000", # Display controller
            "vendor": "0x8086",
            "device": "0x5917",
            "current_link_width": "0", # Integrated graphics often 0 or not applicable
            "firmware_node/path": "\\_SB.PCI0.GFX0"
        }
        
        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path": # handle firmware_node/path
                if "firmware_node" in path:
                    return mock_open(read_data=file_contents["firmware_node/path"])()
            
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            
            # Fallback for other files if needed, or raise FileNotFoundError
            raise FileNotFoundError(f"File not found: {path}")

        monkeypatch.setattr(builtins, "open", custom_open)
        
        # Mock get_pci_path_linux
        monkeypatch.setattr("src.pysysinfo.dumps.linux.gpu.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")
        
        # Mock subprocess.run for lspci
        def mock_run(command, *args, **kwargs):
            if command[0] == "lspci":
                output = (
                    "Slot:	00:02.0\n"
                    "Class:	VGA compatible controller\n"
                    "Vendor:	Intel Corporation\n"
                    "Device:	UHD Graphics 620\n"
                    "SVendor:	Lenovo\n"
                    "SDevice:	Device 225c\n"
                )
                return subprocess.CompletedProcess(command, 0, stdout=output)
            return subprocess.CompletedProcess(command, 1, stdout="")

        monkeypatch.setattr(subprocess, "run", mock_run)

        info = fetch_gpu_info()
        
        assert isinstance(info.status, SuccessStatus)
        assert len(info.modules) == 2 # We mocked 2 devices, both use same file mocks so both appear as GPUs
        
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x8086"
        assert gpu.device_id == "0x5917"
        assert gpu.acpi_path == "\\_SB.PCI0.GFX0"
        assert gpu.manufacturer == "Intel Corporation"
        assert gpu.model == "UHD Graphics 620"
        assert gpu.subsystem_manufacturer == "Lenovo"

    def test_fetch_gpu_info_nvidia(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:01:00.0"])
        
        file_contents = {
            "class": "0x030000",
            "vendor": "0x10de", # Nvidia
            "device": "0x1c03",
            "current_link_width": "16",
            "firmware_node/path": "\\_SB.PCI0.PEG0.PEGP"
        }
        
        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path" and "firmware_node" in path:
                return mock_open(read_data=file_contents["firmware_node/path"])()
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)
        monkeypatch.setattr("src.pysysinfo.dumps.linux.gpu.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")
        
        def mock_run(command, *args, **kwargs):
            if command[0] == "nvidia-smi":
                return subprocess.CompletedProcess(command, 0, stdout="6144\n")
            if command[0] == "lspci":
                output = "Vendor: NVIDIA\nDevice: GeForce GTX 1060\n"
                return subprocess.CompletedProcess(command, 0, stdout=output)
            return subprocess.CompletedProcess(command, 1)

        monkeypatch.setattr(subprocess, "run", mock_run)
        
        info = fetch_gpu_info()
        
        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x10de"
        assert gpu.vram is not None
        assert gpu.vram.capacity == 6144
        assert gpu.pcie_width == 16

    def test_fetch_gpu_info_amd(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:03:00.0"])
        
        file_contents = {
            "class": "0x030000",
            "vendor": "0x1002", # AMD
            "device": "0x731f",
            "current_link_width": "16",
            "firmware_node/path": "\\_SB.PCI0.PEG0.PEGP"
        }
        
        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path" and "firmware_node" in path:
                return mock_open(read_data=file_contents["firmware_node/path"])()
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            # Mock for AMD vram file
            if filename == "mem_info_vram_total":
                 # 8GB in bytes
                return mock_open(read_data=str(8 * 1024 * 1024 * 1024))()
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)
        monkeypatch.setattr("src.pysysinfo.dumps.linux.gpu.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")
        
        # Mock glob for AMD
        monkeypatch.setattr("glob.glob", lambda x: ["/sys/bus/pci/devices/0000:03:00.0/drm/card0/device/mem_info_vram_total"])
        
        def mock_run(command, *args, **kwargs):
            if command[0] == "lspci":
                output = "Vendor: AMD\nDevice: Radeon RX 5700 XT\n"
                return subprocess.CompletedProcess(command, 0, stdout=output)
            return subprocess.CompletedProcess(command, 1)

        monkeypatch.setattr(subprocess, "run", mock_run)
        
        info = fetch_gpu_info()
        
        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x1002"
        assert gpu.vram is not None
        assert gpu.vram.capacity == 8192 # 8GB in MB

    def test_fetch_gpu_info_partial_failure(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:01:00.0"])
        
        # Simulate failure reading vendor file
        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "class":
                return mock_open(read_data="0x030000")()
            if filename == "vendor":
                raise IOError("Permission denied")
            if filename == "device":
                return mock_open(read_data="0x1234")()
            # Fail other files too to test robustness
            raise IOError("File not found")

        monkeypatch.setattr(builtins, "open", custom_open)
        
        # Mock lspci failure
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("lspci not found")
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        info = fetch_gpu_info()
        
        assert isinstance(info.status, PartialStatus)
        assert len(info.modules) == 1
        gpu = info.modules[0]
        # Vendor ID should be None because it failed
        assert gpu.vendor_id is None
        # But we should still have the object
