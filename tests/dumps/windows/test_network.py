import pytest
from unittest.mock import patch, MagicMock
import ctypes

from pysysinfo.dumps.windows.network import fetch_wmi_cmdlet_network_info
from pysysinfo.models.network_models import NICInfo, NetworkInfo
from pysysinfo.models.status_models import StatusType


class TestFetchWmiCmdletNetworkInfo:
    """Test suite for fetch_wmi_cmdlet_network_info function"""

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_successful_network_info_fetch(self, mock_get_location_paths, mock_get_wmi):
        """Test successful fetching of network information"""
        wmi_output = (
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_12345678|"
            "Manufacturer=Intel|"
            "Name=Intel Ethernet Controller\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.return_value = ["PCIROOT(0)#PCI(0,0)", "ACPI(_SB_)#ACPI(PCI0)"]
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.SUCCESS
        assert len(result.modules) == 1
        assert result.modules[0].name == "Intel Ethernet Controller"
        assert result.modules[0].manufacturer == "Intel"
        assert result.modules[0].vendor_id == "8086"
        assert result.modules[0].device_id == "1234"

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_multiple_network_adapters(self, mock_get_location_paths, mock_get_wmi):
        """Test fetching information for multiple network adapters"""
        wmi_output = (
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_12345678|"
            "Manufacturer=Intel|"
            "Name=Intel Ethernet Controller\n"
            "PNPDeviceID=PCI\\VEN_10EC&DEV_5678&SUBSYS_87654321|"
            "Manufacturer=Realtek|"
            "Name=Realtek RTL8111\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.side_effect = [
            ["PCIROOT(0)#PCI(0,0)", "ACPI(_SB_)#ACPI(PCI0)"],
            ["PCIROOT(0)#PCI(2,0)", "ACPI(_SB_)#ACPI(PCI0)"]
        ]
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert len(result.modules) == 2
        assert result.modules[0].manufacturer == "Intel"
        assert result.modules[1].manufacturer == "Realtek"

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_usb_network_adapter(self, mock_get_location_paths, mock_get_wmi):
        """Test fetching USB network adapter with VID/PID"""
        wmi_output = (
            "PNPDeviceID=USB\\VID_0BDA&PID_8153&MI_00|"
            "Manufacturer=Realtek|"
            "Name=USB Ethernet\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.return_value = ["USBROOT(0)#USB(1)", "ACPI(_SB_)#ACPI(RHUB)"]
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert len(result.modules) == 1
        assert result.modules[0].vendor_id == "0BDA"
        assert result.modules[0].device_id == "8153"

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_empty_wmi_output(self, mock_get_location_paths, mock_get_wmi):
        """Test handling of empty WMI output"""
        def set_buffer(query, root, buffer, size):
            buffer.value = b""
        
        mock_get_wmi.side_effect = set_buffer
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.SUCCESS
        assert len(result.modules) == 0

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_malformed_wmi_output(self, mock_get_location_paths, mock_get_wmi):
        """Test handling of malformed WMI output"""
        wmi_output = "INVALID_DATA_WITHOUT_PIPES_OR_EQUALS"
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.SUCCESS
        assert len(result.modules) == 0

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    def test_wmi_decoding_error(self, mock_get_wmi):
        """Test handling of WMI output decoding errors"""
        invalid_utf8 = b'\xff\xfe'
        
        def set_buffer(query, root, buffer, size):
            for i, byte in enumerate(invalid_utf8):
                buffer[i] = byte
        
        mock_get_wmi.side_effect = set_buffer
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.FAILED
        assert "Failed to decode WMI output" in result.status.messages

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_missing_optional_fields(self, mock_get_location_paths, mock_get_wmi):
        """Test handling of missing optional fields in WMI output"""
        wmi_output = (
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_12345678|"
            "Name=Network Adapter\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.return_value = []
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert len(result.modules) == 1
        assert result.modules[0].manufacturer is None
        assert result.modules[0].name == "Network Adapter"

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_location_paths_with_insufficient_paths(self, mock_get_location_paths, mock_get_wmi):
        """Test handling when location_paths returns fewer than expected items"""
        wmi_output = (
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_12345678|"
            "Manufacturer=Intel|"
            "Name=Intel Adapter\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        # Return only one path instead of two
        mock_get_location_paths.return_value = ["PCIROOT(0)#PCI(0,0)"]
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert len(result.modules) == 1
        assert result.modules[0].pci_path is not None
        assert result.modules[0].acpi_path is None or result.modules[0].acpi_path == ""

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_location_paths_returns_none(self, mock_get_location_paths, mock_get_wmi):
        """Test handling when get_location_paths returns None"""
        wmi_output = (
            "PNPDeviceID=UNKNOWN\\VEN_1234&DEV_5678|"
            "Manufacturer=Unknown|"
            "Name=Unknown Device\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.return_value = None
        
        result = fetch_wmi_cmdlet_network_info()
        
        # Should handle None gracefully with list concatenation
        assert len(result.modules) == 1

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_pnp_device_id_without_vendor_device_ids(self, mock_get_location_paths, mock_get_wmi):
        """Test handling of PNP Device ID without standard vendor/device identifiers"""
        wmi_output = (
            "PNPDeviceID=UNKNOWN\\ADAPTER123|"
            "Manufacturer=Generic|"
            "Name=Generic NIC\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.return_value = []
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert len(result.modules) == 1
        assert result.modules[0].vendor_id is None
        assert result.modules[0].device_id is None

    @patch('pysysinfo.dumps.windows.network.GetWmiInfo')
    @patch('pysysinfo.dumps.windows.network.get_location_paths')
    def test_multiple_adapters_with_mixed_pnp_formats(self, mock_get_location_paths, mock_get_wmi):
        """Test multiple adapters with different PNP Device ID formats"""
        wmi_output = (
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_12345678|"
            "Manufacturer=Intel|"
            "Name=Intel Ethernet\n"
            "PNPDeviceID=USB\\VID_0BDA&PID_8153&MI_00|"
            "Manufacturer=Realtek|"
            "Name=USB Realtek\n"
            "PNPDeviceID=UNKNOWN\\ADAPTER456|"
            "Manufacturer=Unknown|"
            "Name=Unknown NIC\n"
        )
        
        def set_buffer(query, root, buffer, size):
            buffer.value = wmi_output.encode('utf-8')
        
        mock_get_wmi.side_effect = set_buffer
        mock_get_location_paths.side_effect = [
            ["PCIROOT(0)#PCI(0,0)", "ACPI(_SB_)"],
            ["USBROOT(0)#USB(1)", "ACPI(_SB_)"],
            []
        ]
        
        result = fetch_wmi_cmdlet_network_info()
        
        assert len(result.modules) == 3
        assert result.modules[0].vendor_id == "8086"
        assert result.modules[1].vendor_id == "0BDA"
        assert result.modules[2].vendor_id is None


class TestNetworkInfoModel:
    """Test suite for NetworkInfo model"""

    def test_network_info_initialization(self):
        """Test NetworkInfo model initialization"""
        network_info = NetworkInfo()
        
        assert isinstance(network_info.modules, list)
        assert len(network_info.modules) == 0

    def test_nic_info_initialization(self):
        """Test NICInfo model initialization"""
        nic = NICInfo()
        
        assert nic.name is None
        assert nic.device_id is None
        assert nic.vendor_id is None
        assert nic.acpi_path is None
        assert nic.pci_path is None
        assert nic.manufacturer is None

    def test_nic_info_with_values(self):
        """Test NICInfo model with values"""
        nic = NICInfo(
            name="Intel Ethernet",
            device_id="1234",
            vendor_id="8086",
            acpi_path="ACPI(_SB_)#ACPI(PCI0)",
            pci_path="PCIROOT(0)#PCI(0,0)",
            manufacturer="Intel"
        )
        
        assert nic.name == "Intel Ethernet"
        assert nic.device_id == "1234"
        assert nic.vendor_id == "8086"
        assert nic.acpi_path == "ACPI(_SB_)#ACPI(PCI0)"
        assert nic.pci_path == "PCIROOT(0)#PCI(0,0)"
        assert nic.manufacturer == "Intel"

    def test_network_info_append_modules(self):
        """Test appending NICInfo modules to NetworkInfo"""
        network_info = NetworkInfo()
        nic1 = NICInfo(name="NIC1", manufacturer="Intel")
        nic2 = NICInfo(name="NIC2", manufacturer="Realtek")
        
        network_info.modules.append(nic1)
        network_info.modules.append(nic2)
        
        assert len(network_info.modules) == 2
        assert network_info.modules[0].name == "NIC1"
        assert network_info.modules[1].name == "NIC2"
