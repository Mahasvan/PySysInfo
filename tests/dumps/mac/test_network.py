import plistlib
from unittest.mock import patch, MagicMock

import pytest

from pysysinfo.dumps.mac.network import (
    _fetch_controllers,
    _fetch_ethernet_details,
    _fetch_airport_details,
    _fetch_system_profiler_details,
    fetch_network_info,
)
from pysysinfo.models.network_models import NetworkInfo, NICInfo


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_subprocess_result(stdout_str="", stdout_bytes=None):
    mock_result = MagicMock()
    if stdout_bytes is not None:
        mock_result.stdout = stdout_bytes
    else:
        mock_result.stdout = stdout_str.encode()
    return mock_result


def _make_network_plist(items):
    """Build a fake SPNetworkDataType plist structure."""
    return plistlib.dumps([{"_items": items}], fmt=plistlib.FMT_XML)


def _make_ethernet_plist(items):
    """Build a fake SPEthernetDataType plist structure."""
    return plistlib.dumps([{"_items": items}], fmt=plistlib.FMT_XML)


def _make_airport_plist(items):
    """Build a fake SPAirPortDataType plist structure."""
    return plistlib.dumps([{"_items": items}], fmt=plistlib.FMT_XML)


# ── _fetch_controllers ───────────────────────────────────────────────────────

class TestFetchControllers:

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_returns_interface_list(self, mock_run):
        mock_run.return_value = _make_subprocess_result("en0 en1 en2")
        result = _fetch_controllers()
        assert result == ["en0", "en1", "en2"]

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_single_interface(self, mock_run):
        mock_run.return_value = _make_subprocess_result("en0")
        result = _fetch_controllers()
        assert result == ["en0"]

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_empty_output_returns_empty_list(self, mock_run):
        mock_run.return_value = _make_subprocess_result("")
        result = _fetch_controllers()
        assert result == []

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_subprocess_failure_propagates(self, mock_run):
        """
        BUG 2: No try/except around subprocess call.
        """
        mock_run.side_effect = FileNotFoundError("ipconfig not found")
        with pytest.raises(FileNotFoundError):
            _fetch_controllers()


# ── _fetch_ethernet_details ──────────────────────────────────────────────────

class TestFetchEthernetDetails:

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_single_ethernet_controller(self, mock_run):
        plist_data = _make_ethernet_plist([{
            "spethernet_BSD_Device_Name": "en0",
            "spethernet_vendor-id": "0x8086",
            "spethernet_vendor_name": "Intel",
            "spethernet_product-id": "0x15B8",
        }])
        mock_run.return_value = MagicMock(stdout=plist_data)

        result = _fetch_ethernet_details()
        assert "en0" in result
        assert result["en0"].vendor_id == "0x8086"
        assert result["en0"].manufacturer == "Intel"
        assert result["en0"].device_id == "0x15B8"

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_multiple_ethernet_controllers(self, mock_run):
        plist_data = _make_ethernet_plist([
            {
                "spethernet_BSD_Device_Name": "en0",
                "spethernet_vendor-id": "0x8086",
                "spethernet_vendor_name": "Intel",
                "spethernet_product-id": "0x15B8",
            },
            {
                "spethernet_BSD_Device_Name": "en3",
                "spethernet_vendor-id": "0x14E4",
                "spethernet_vendor_name": "Broadcom",
                "spethernet_product-id": "0x1682",
            },
        ])
        mock_run.return_value = MagicMock(stdout=plist_data)

        result = _fetch_ethernet_details()
        assert len(result) == 2
        assert "en0" in result
        assert "en3" in result

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_subprocess_failure_propagates(self, mock_run):
        """BUG 2: No error handling in _fetch_ethernet_details."""
        mock_run.side_effect = FileNotFoundError("system_profiler not found")
        with pytest.raises(FileNotFoundError):
            _fetch_ethernet_details()


# ── _fetch_airport_details ───────────────────────────────────────────────────

class TestFetchAirportDetails:

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_single_wifi_card(self, mock_run):
        plist_data = _make_airport_plist([{
            "spairport_airport_interfaces": [{
                "_name": "en1",
                "spairport_wireless_card_type": "Wi-Fi  (0x14E4, 0x4331)",
            }]
        }])
        mock_run.return_value = MagicMock(stdout=plist_data)

        result = _fetch_airport_details()
        assert "en1" in result
        assert result["en1"].vendor_id == "0x14E4"
        assert result["en1"].device_id == "0x4331"

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_awdl_interface_skipped(self, mock_run):
        """AWDL interfaces lack spairport_wireless_card_type and should be skipped."""
        plist_data = _make_airport_plist([{
            "spairport_airport_interfaces": [{
                "_name": "awdl0",
                # No spairport_wireless_card_type key
            }]
        }])
        mock_run.return_value = MagicMock(stdout=plist_data)

        result = _fetch_airport_details()
        assert "awdl0" not in result

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_card_type_without_vendor_device_pattern_skipped(self, mock_run):
        plist_data = _make_airport_plist([{
            "spairport_airport_interfaces": [{
                "_name": "en1",
                "spairport_wireless_card_type": "Wi-Fi Unknown Type",
            }]
        }])
        mock_run.return_value = MagicMock(stdout=plist_data)

        result = _fetch_airport_details()
        assert result == {}

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_subprocess_failure_propagates(self, mock_run):
        """BUG 2: No error handling."""
        mock_run.side_effect = FileNotFoundError("system_profiler not found")
        with pytest.raises(FileNotFoundError):
            _fetch_airport_details()


# ── _fetch_system_profiler_details ───────────────────────────────────────────

class TestFetchSystemProfilerDetails:

    @patch("pysysinfo.dumps.mac.network._fetch_ethernet_details")
    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_single_ethernet_nic(self, mock_run, mock_eth):
        network_plist = _make_network_plist([{
            "interface": "en0",
            "_name": "Ethernet",
            "Ethernet": {"MAC Address": "aa:bb:cc:dd:ee:ff"},
            "type": "Ethernet",
            "IPv4": {"Addresses": ["192.168.1.100"]},
        }])
        mock_run.return_value = MagicMock(stdout=network_plist)
        mock_eth.return_value = {
            "en0": NICInfo(vendor_id="0x8086", manufacturer="Intel", device_id="0x15B8")
        }

        result = _fetch_system_profiler_details(["en0"])
        assert len(result.modules) == 1
        m = result.modules[0]
        assert m.interface == "en0"
        assert m.name == "Ethernet"
        assert m.mac_address == "aa:bb:cc:dd:ee:ff"
        assert m.type == "Ethernet"
        assert m.ip_address == "192.168.1.100"
        assert m.vendor_id == "0x8086"
        assert m.manufacturer == "Intel"

    @patch("pysysinfo.dumps.mac.network._fetch_airport_details")
    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_single_wifi_nic(self, mock_run, mock_air):
        network_plist = _make_network_plist([{
            "interface": "en1",
            "_name": "Wi-Fi",
            "Ethernet": {"MAC Address": "11:22:33:44:55:66"},
            "type": "AirPort",
        }])
        mock_run.return_value = MagicMock(stdout=network_plist)
        mock_air.return_value = {
            "en1": NICInfo(vendor_id="0x14E4", device_id="0x4331")
        }

        result = _fetch_system_profiler_details(["en1"])
        assert len(result.modules) == 1
        m = result.modules[0]
        assert m.type == "AirPort"
        assert m.vendor_id == "0x14E4"

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_interface_not_in_valid_list_is_skipped(self, mock_run):
        network_plist = _make_network_plist([{
            "interface": "en5",
            "_name": "USB Ethernet",
            "Ethernet": {"MAC Address": "aa:bb:cc:dd:ee:ff"},
            "type": "Ethernet",
        }])
        mock_run.return_value = MagicMock(stdout=network_plist)

        result = _fetch_system_profiler_details(["en0", "en1"])
        assert result.modules == []

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_no_mac_address_skipped(self, mock_run):
        """Devices without MAC address are skipped (unplugged devices)."""
        network_plist = _make_network_plist([{
            "interface": "en0",
            "_name": "Ethernet",
            "type": "Ethernet",
        }])
        mock_run.return_value = MagicMock(stdout=network_plist)

        result = _fetch_system_profiler_details(["en0"])
        assert result.modules == []

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_no_ip_address_still_included(self, mock_run):
        network_plist = _make_network_plist([{
            "interface": "en0",
            "_name": "Ethernet",
            "Ethernet": {"MAC Address": "aa:bb:cc:dd:ee:ff"},
            "type": "Ethernet",
        }])
        mock_run.return_value = MagicMock(stdout=network_plist)

        result = _fetch_system_profiler_details(["en0"])
        assert len(result.modules) == 1
        assert result.modules[0].ip_address is None

    @patch("pysysinfo.dumps.mac.network._fetch_ethernet_details")
    @patch("pysysinfo.dumps.mac.network._fetch_airport_details")
    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_mixed_ethernet_and_wifi(self, mock_run, mock_air, mock_eth):
        network_plist = _make_network_plist([
            {
                "interface": "en0",
                "_name": "Ethernet",
                "Ethernet": {"MAC Address": "aa:bb:cc:dd:ee:ff"},
                "type": "Ethernet",
            },
            {
                "interface": "en1",
                "_name": "Wi-Fi",
                "Ethernet": {"MAC Address": "11:22:33:44:55:66"},
                "type": "AirPort",
            },
        ])
        mock_run.return_value = MagicMock(stdout=network_plist)
        mock_eth.return_value = {"en0": NICInfo(vendor_id="0x8086")}
        mock_air.return_value = {"en1": NICInfo(vendor_id="0x14E4")}

        result = _fetch_system_profiler_details(["en0", "en1"])
        assert len(result.modules) == 2


# ── Missing _items key handled gracefully ─────────────────────────────────

class TestMissingItemsKey:

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_missing_items_key_returns_empty(self, mock_run):
        bad_plist = plistlib.dumps([{
            "not_items": [{"interface": "en0"}]
        }], fmt=plistlib.FMT_XML)
        mock_run.return_value = MagicMock(stdout=bad_plist)

        result = _fetch_system_profiler_details(["en0"])
        assert result.modules == []


# ── Empty controller list ─────────────────────────────────────────────────

class TestEmptyControllers:

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_empty_controllers_passes_empty_list(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd == ["ipconfig", "getiflist"]:
                return _make_subprocess_result("")
            if cmd[0] == "system_profiler":
                return MagicMock(stdout=_make_network_plist([]))
            raise FileNotFoundError(f"Unexpected: {cmd}")

        mock_run.side_effect = side_effect

        result = fetch_network_info()
        assert isinstance(result, NetworkInfo)
        assert result.modules == []


# ── fetch_network_info ───────────────────────────────────────────────────────

class TestFetchNetworkInfo:

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_returns_network_info_type(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd == ["ipconfig", "getiflist"]:
                return _make_subprocess_result("en0")
            if cmd[0] == "system_profiler":
                return MagicMock(stdout=_make_network_plist([]))
            raise FileNotFoundError(f"Unexpected: {cmd}")

        mock_run.side_effect = side_effect

        result = fetch_network_info()
        assert isinstance(result, NetworkInfo)

    @patch("pysysinfo.dumps.mac.network.subprocess.run")
    def test_ipconfig_failure_propagates(self, mock_run):
        """BUG 2: No error handling around subprocess calls in fetch_network_info."""
        mock_run.side_effect = FileNotFoundError("ipconfig not found")
        with pytest.raises(FileNotFoundError):
            fetch_network_info()
