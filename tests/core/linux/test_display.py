import builtins
import os
from unittest.mock import mock_open, patch

import pytest

from hwprobe.models.display_models import DisplayModuleInfo
from hwprobe.core.linux.display import (
    _extract_pci_bdf_from_sysfs_path,
    _fetch_individual_monitor_info,
    fetch_display_info,
)


class TestExtractPciBdfFromSysfsPath:
    def test_returns_last_bdf_in_chain(self):
        path = "/sys/devices/pci0000:00/0000:00:02.0/0000:05:00.0/drm/card0"
        assert _extract_pci_bdf_from_sysfs_path(path) == "0000:05:00.0"

    def test_single_bdf(self):
        path = "/sys/devices/pci0000:00/0000:00:02.0/drm/card0"
        assert _extract_pci_bdf_from_sysfs_path(path) == "0000:00:02.0"

    def test_no_pci_device(self):
        path = "/sys/devices/platform/simple-framebuffer/drm/card0"
        assert _extract_pci_bdf_from_sysfs_path(path) is None

    def test_empty_path(self):
        assert _extract_pci_bdf_from_sysfs_path("") is None


class TestFetchIndividualMonitorInfo:
    DEVICE_PATH = "/sys/class/drm/card0/card0-eDP-1"
    EDID_PATH = os.path.join(DEVICE_PATH, "edid")
    ACPI_PATH = os.path.join(DEVICE_PATH, "firmware_node", "path")

    def _patch_exists(self, monkeypatch, paths):
        monkeypatch.setattr(os.path, "exists", lambda p: p in paths)

    def test_returns_none_when_edid_missing(self, monkeypatch):
        self._patch_exists(monkeypatch, set())
        assert _fetch_individual_monitor_info(self.DEVICE_PATH) is None

    def test_returns_none_when_edid_empty(self, monkeypatch):
        self._patch_exists(monkeypatch, {self.EDID_PATH})
        monkeypatch.setattr(
            builtins, "open",
            lambda *a, **kw: mock_open(read_data=b"")(),
        )
        assert _fetch_individual_monitor_info(self.DEVICE_PATH) is None

    def test_pci_path_resolved_from_gpu_endpoint(self, monkeypatch):
        self._patch_exists(monkeypatch, {self.EDID_PATH})
        monkeypatch.setattr(
            builtins, "open",
            lambda *a, **kw: mock_open(read_data=b"\x01\x02")(),
        )
        monkeypatch.setattr(
            "hwprobe.core.linux.display.parse_edid",
            lambda _: DisplayModuleInfo(name="Internal Display"),
        )
        monkeypatch.setattr(
            os.path, "realpath",
            lambda _: "/sys/devices/pci0000:00/0000:00:02.0/0000:06:00.0/drm/card0",
        )

        pci_calls = []
        monkeypatch.setattr(
            "hwprobe.core.linux.display.pci_path_linux",
            lambda slot: (pci_calls.append(slot), "PciRoot(0x0)/Pci(0x6,0x0)")[-1],
        )

        monitor = _fetch_individual_monitor_info(self.DEVICE_PATH)

        assert monitor is not None
        assert pci_calls == ["0000:06:00.0"]
        assert monitor.pci_path == "PciRoot(0x0)/Pci(0x6,0x0)"

    def test_no_pci_path_for_non_pci_parent(self, monkeypatch):
        self._patch_exists(monkeypatch, {self.EDID_PATH})
        monkeypatch.setattr(
            builtins, "open",
            lambda *a, **kw: mock_open(read_data=b"\x01\x02")(),
        )
        monkeypatch.setattr(
            "hwprobe.core.linux.display.parse_edid",
            lambda _: DisplayModuleInfo(name="Panel"),
        )
        monkeypatch.setattr(
            os.path, "realpath",
            lambda _: "/sys/devices/platform/simple-framebuffer/drm/card0",
        )

        pci_calls = []
        monkeypatch.setattr(
            "hwprobe.core.linux.display.pci_path_linux",
            lambda slot: pci_calls.append(slot),
        )

        monitor = _fetch_individual_monitor_info(self.DEVICE_PATH)

        assert monitor is not None
        assert pci_calls == []
        assert monitor.pci_path is None

    def test_acpi_path_populated_when_firmware_node_exists(self, monkeypatch):
        self._patch_exists(monkeypatch, {self.EDID_PATH, self.ACPI_PATH})

        real_open = builtins.open
        def fake_open(path, *args, **kwargs):
            if path == self.EDID_PATH:
                return mock_open(read_data=b"\x01\x02")()
            if path == self.ACPI_PATH:
                return mock_open(read_data=r"\_SB.PCI0.GFX0.DD1F")()
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", fake_open)
        monkeypatch.setattr(
            "hwprobe.core.linux.display.parse_edid",
            lambda _: DisplayModuleInfo(name="Display"),
        )
        monkeypatch.setattr(
            os.path, "realpath",
            lambda _: "/sys/devices/pci0000:00/0000:00:02.0/drm/card0",
        )
        monkeypatch.setattr(
            "hwprobe.core.linux.display.pci_path_linux",
            lambda slot: "PciRoot(0x0)/Pci(0x2,0x0)",
        )

        monitor = _fetch_individual_monitor_info(self.DEVICE_PATH)

        assert monitor is not None
        assert monitor.acpi_path == r"\_SB.PCI0.GFX0.DD1F"


class TestFetchDisplayInfo:
    def test_collects_monitors_from_drm(self, monkeypatch):
        monkeypatch.setattr(
            os, "listdir",
            lambda path: {
                "/sys/class/drm": ["card0", "renderD128", "version"],
                "/sys/class/drm/card0": ["card0-eDP-1", "card0-HDMI-A-1", "device"],
            }.get(path, []),
        )
        monkeypatch.setattr(
            "hwprobe.core.linux.display._fetch_individual_monitor_info",
            lambda path: DisplayModuleInfo(name=os.path.basename(path)),
        )

        info = fetch_display_info()

        assert len(info.modules) == 2
        names = {m.name for m in info.modules}
        assert names == {"card0-eDP-1", "card0-HDMI-A-1"}

    def test_skips_monitors_returning_none(self, monkeypatch):
        monkeypatch.setattr(
            os, "listdir",
            lambda path: {
                "/sys/class/drm": ["card0"],
                "/sys/class/drm/card0": ["card0-eDP-1"],
            }.get(path, []),
        )
        monkeypatch.setattr(
            "hwprobe.core.linux.display._fetch_individual_monitor_info",
            lambda path: None,
        )

        info = fetch_display_info()

        assert len(info.modules) == 0
