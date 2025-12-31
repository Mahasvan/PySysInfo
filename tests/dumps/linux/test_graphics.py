import builtins
import os
import subprocess
from unittest.mock import mock_open

from pysysinfo.dumps.linux.graphics import fetch_graphics_info, get_pcie_gen, fetch_vram_amd
from pysysinfo.models.status_models import FailedStatus, PartialStatus, SuccessStatus


class TestLinuxGraphics:

    # Tests from original test_graphics.py for helper functions
    def test_get_pcie_gen_success(self, monkeypatch):
        device = "0000:01:00.0"
        path = f"/sys/bus/pci/devices/{device}/current_link_speed"

        monkeypatch.setattr(os.path, "exists", lambda x: x == path)

        def mock_open_func(file, *args, **kwargs):
            if file == path:
                return mock_open(read_data="16.0 GT/s")()
            raise FileNotFoundError(file)

        monkeypatch.setattr(builtins, "open", mock_open_func)

        gen = get_pcie_gen(device)
        assert gen == 4

    def test_get_pcie_gen_unknown_speed(self, monkeypatch):
        device = "0000:01:00.0"
        path = f"/sys/bus/pci/devices/{device}/current_link_speed"

        monkeypatch.setattr(os.path, "exists", lambda x: x == path)

        def mock_open_func(file, *args, **kwargs):
            if file == path:
                return mock_open(read_data="100.0 GT/s")()
            raise FileNotFoundError(file)

        monkeypatch.setattr(builtins, "open", mock_open_func)

        gen = get_pcie_gen(device)
        assert gen is None

    def test_get_pcie_gen_file_not_found(self, monkeypatch):
        device = "0000:01:00.0"
        monkeypatch.setattr(os.path, "exists", lambda x: False)

        gen = get_pcie_gen(device)
        assert gen is None

    def test_fetch_vram_amd_success(self, monkeypatch):
        device = "0000:03:00.0"
        vram_path = f"/sys/bus/pci/devices/{device}/drm/card0/device/mem_info_vram_total"

        monkeypatch.setattr("glob.glob", lambda x: [vram_path])

        def mock_open_func(file, *args, **kwargs):
            if file == vram_path:
                # 8GB in bytes
                return mock_open(read_data=str(8 * 1024 * 1024 * 1024))()
            raise FileNotFoundError(file)

        monkeypatch.setattr(builtins, "open", mock_open_func)

        vram_mb = fetch_vram_amd(device)
        assert vram_mb == 8192

    def test_fetch_vram_amd_no_file(self, monkeypatch):
        device = "0000:03:00.0"
        monkeypatch.setattr("glob.glob", lambda x: [])

        vram_mb = fetch_vram_amd(device)
        assert vram_mb is None

    # Tests merged from test_gpu.py
    def test_fetch_graphics_info_root_not_found(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: False)

        info = fetch_graphics_info()

        assert isinstance(info.status, FailedStatus)
        assert "not found" in info.status.messages[0]
        assert len(info.modules) == 0

    def test_fetch_graphics_info_success_generic(self, monkeypatch):
        # Mock os.path.exists
        monkeypatch.setattr(os.path, "exists", lambda x: True)

        # Mock os.listdir
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:01:00.0", "0000:00:02.0"])

        # Mock open
        file_contents = {
            "class": "0x030000",  # Display controller
            "vendor": "0x8086",
            "device": "0x5917",
            "current_link_width": "0",  # Integrated graphics often 0 or not applicable
            "firmware_node/path": "\\_SB.PCI0.GFX0"
        }

        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path":  # handle firmware_node/path
                if "firmware_node" in path:
                    return mock_open(read_data=file_contents["firmware_node/path"])()

            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()

            # Fallback for other files if needed, or raise FileNotFoundError
            raise FileNotFoundError(f"File not found: {path}")

        monkeypatch.setattr(builtins, "open", custom_open)

        # Mock get_pci_path_linux
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")

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

        info = fetch_graphics_info()

        assert isinstance(info.status, SuccessStatus)
        assert len(info.modules) == 2  # We mocked 2 devices, both use same file mocks so both appear as GPUs

        gpu = info.modules[0]
        assert gpu.vendor_id == "0x8086"
        assert gpu.device_id == "0x5917"
        assert gpu.acpi_path == "\\_SB.PCI0.GFX0"
        assert gpu.manufacturer == "Intel Corporation"
        assert gpu.name == "UHD Graphics 620"
        assert gpu.subsystem_manufacturer == "Lenovo"

    def test_fetch_graphics_info_nvidia(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:01:00.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x10de",  # Nvidia
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
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")

        def mock_run(command, *args, **kwargs):
            if command[0] == "nvidia-smi":
                return subprocess.CompletedProcess(command, 0, stdout="GeForce GTX 1060, 16, 3, 6144\n")
            if command[0] == "lspci":
                output = "Vendor: NVIDIA\nDevice: GeForce GTX 1060\n"
                return subprocess.CompletedProcess(command, 0, stdout=output)
            return subprocess.CompletedProcess(command, 1)

        monkeypatch.setattr(subprocess, "run", mock_run)

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x10de"
        assert gpu.vram is not None
        assert gpu.vram.capacity == 6144
        assert gpu.pcie_width == 16

    def test_fetch_graphics_info_amd(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:03:00.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x1002",  # AMD
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
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")

        # Mock glob for AMD
        monkeypatch.setattr("glob.glob",
                            lambda x: ["/sys/bus/pci/devices/0000:03:00.0/drm/card0/device/mem_info_vram_total"])

        def mock_run(command, *args, **kwargs):
            if command[0] == "lspci":
                output = "Vendor: AMD\nDevice: Radeon RX 5700 XT\n"
                return subprocess.CompletedProcess(command, 0, stdout=output)
            return subprocess.CompletedProcess(command, 1)

        monkeypatch.setattr(subprocess, "run", mock_run)

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x1002"
        assert gpu.vram is not None
        assert gpu.vram.capacity == 8192  # 8GB in MB

    def test_fetch_graphics_info_partial_failure(self, monkeypatch):
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

        info = fetch_graphics_info()

        assert isinstance(info.status, PartialStatus)
        assert len(info.modules) == 1
        gpu = info.modules[0]
        # Vendor ID should be None because it failed
        assert gpu.vendor_id is None
        # But we should still have the object

    def test_fetch_graphics_info_skip_non_display(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:04:00.0"])

        # Class 0x020000 is Network Controller (Base class 0x02)
        file_contents = {
            "class": "0x020000",
        }

        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)

        info = fetch_graphics_info()

        # Should be skipped, so no modules found
        assert len(info.modules) == 0
        assert isinstance(info.status, SuccessStatus)

    def test_fetch_graphics_info_amd_vram_failure(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:03:00.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x1002",  # AMD
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
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")

        # Mock glob to return empty list (VRAM file not found)
        monkeypatch.setattr("glob.glob", lambda x: [])

        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=""))

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x1002"
        # VRAM should be None because fetch failed
        assert gpu.vram is None

    def test_fetch_graphics_info_nvidia_vram_failure(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:01:00.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x10de",  # Nvidia
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
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")

        # Mock nvidia-smi failure
        def mock_run(command, *args, **kwargs):
            if command[0] == "nvidia-smi":
                # Simulate failure
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0, stdout="")

        monkeypatch.setattr(subprocess, "run", mock_run)

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x10de"
        assert gpu.vram is None
        # Should have partial status due to vram failure
        assert isinstance(info.status, PartialStatus)
        assert any("Could not get additional GPU info" in msg for msg in info.status.messages)

    def test_fetch_graphics_info_lspci_missing_fields(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:00:02.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x8086",
            "device": "0x5917",
            "current_link_width": "0",
            "firmware_node/path": "\\_SB.PCI0.GFX0"
        }

        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path" and "firmware_node" in path:
                return mock_open(read_data=file_contents["firmware_node/path"])()
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")

        def mock_run(command, *args, **kwargs):
            if command[0] == "lspci":
                # Output missing SVendor and SDevice
                output = (
                    "Slot:	00:02.0\n"
                    "Class:	VGA compatible controller\n"
                    "Vendor:	Intel Corporation\n"
                    "Device:	UHD Graphics 620\n"
                )
                return subprocess.CompletedProcess(command, 0, stdout=output)
            return subprocess.CompletedProcess(command, 1)

        monkeypatch.setattr(subprocess, "run", mock_run)

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.manufacturer == "Intel Corporation"
        assert gpu.name == "UHD Graphics 620"
        assert gpu.subsystem_manufacturer is None
        assert gpu.subsystem_model is None

    def test_fetch_graphics_info_acpi_path_failure(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:00:02.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x8086",
            "device": "0x5917",
            "current_link_width": "0",
        }

        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path" and "firmware_node" in path:
                # Simulate missing ACPI path file
                raise FileNotFoundError("No ACPI path")
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)
        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", lambda x: f"/PCI0@0/{x}")
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=""))

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.vendor_id == "0x8086"
        assert gpu.acpi_path is None
        # Should be partial status
        assert isinstance(info.status, PartialStatus)
        assert any("ACPI path" in msg for msg in info.status.messages)

    def test_fetch_vram_amd_exception(self, monkeypatch):
        # Directly test the helper function
        monkeypatch.setattr("glob.glob", lambda x: (_ for _ in ()).throw(Exception("Glob failed")))

        from pysysinfo.dumps.linux.graphics import fetch_vram_amd
        assert fetch_vram_amd("0000:00:00.0") is None

    def test_fetch_graphics_info_pci_path_failure(self, monkeypatch):
        monkeypatch.setattr(os.path, "exists", lambda x: True)
        monkeypatch.setattr(os, "listdir", lambda x: ["0000:00:02.0"])

        file_contents = {
            "class": "0x030000",
            "vendor": "0x8086",
            "device": "0x5917",
            "current_link_width": "0",
            "firmware_node/path": "\\_SB.PCI0.GFX0"
        }

        def custom_open(path, *args, **kwargs):
            filename = os.path.basename(path)
            if filename == "path" and "firmware_node" in path:
                return mock_open(read_data=file_contents["firmware_node/path"])()
            if filename in file_contents:
                return mock_open(read_data=file_contents[filename])()
            raise FileNotFoundError(path)

        monkeypatch.setattr(builtins, "open", custom_open)

        # Mock get_pci_path_linux to fail
        def mock_get_pci_path(device):
            raise Exception("PCI path failed")

        monkeypatch.setattr("pysysinfo.dumps.linux.graphics.get_pci_path_linux", mock_get_pci_path)
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=""))

        info = fetch_graphics_info()

        assert len(info.modules) == 1
        gpu = info.modules[0]
        assert gpu.pci_path is None
        assert isinstance(info.status, PartialStatus)
        assert any("PCI path" in msg for msg in info.status.messages)
