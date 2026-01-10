import pytest
from unittest.mock import patch
import ctypes

from pysysinfo.dumps.windows.network import fetch_network_info_fast
from pysysinfo.models.network_models import NICInfo, NetworkInfo
from pysysinfo.models.status_models import StatusType, Status


class TestFetchWmiCmdletNetworkInfo:
    """Test suite for fetch_wmi_cmdlet_network_info function"""

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_successful_pci_network_adapter(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test successful fetching of a single PCI network adapter"""
        wmi_output = (
            "Manufacturer=Intel|"
            "PNPDeviceID=PCI\\VEN_8086&DEV_1F42&SUBSYS_00000000|"
            "Name=Intel Ethernet Controller I219-V|"
            "FriendlyName=Ethernet\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.return_value = [
            "PCIROOT(0)#PCI(0,0)",
            "ACPI(_SB_)#ACPI(PCI0)",
        ]

        result = fetch_network_info_fast()

        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.SUCCESS
        assert len(result.modules) == 1
        assert result.modules[0].name == "Intel Ethernet Controller I219-V"
        assert result.modules[0].manufacturer == "Intel"
        assert result.modules[0].vendor_id == "8086"
        assert result.modules[0].device_id == "1F42"
        assert result.modules[0].pci_path is not None
        assert result.modules[0].acpi_path is not None

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_successful_usb_network_adapter(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test successful fetching of a USB network adapter"""
        wmi_output = (
            "Manufacturer=Realtek|"
            "PNPDeviceID=USB\\VID_0BDA&PID_8153&MI_00|"
            "Name=Realtek USB 10/100/1000 LAN Adapter|"
            "FriendlyName=USB Ethernet\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.return_value = [
            "USBROOT(0)#USB(1,1)",
            "ACPI(_SB_)#ACPI(RHUB)",
        ]

        result = fetch_network_info_fast()

        assert len(result.modules) == 1
        assert result.modules[0].vendor_id == "0BDA"
        assert result.modules[0].device_id == "8153"
        assert result.modules[0].manufacturer == "Realtek"

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_multiple_network_adapters(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test fetching multiple network adapters (PCI and USB)"""
        wmi_output = (
            "Manufacturer=Intel|"
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_00000000|"
            "Name=Intel Ethernet|"
            "FriendlyName=Ethernet 1\n"
            "Manufacturer=Realtek|"
            "PNPDeviceID=USB\\VID_0BDA&PID_8153&MI_00|"
            "Name=Realtek USB Adapter|"
            "FriendlyName=USB Ethernet\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.side_effect = [
            ["PCIROOT(0)#PCI(0,0)", "ACPI(_SB_)"],
            ["USBROOT(0)#USB(1)", "ACPI(_SB_)"],
        ]

        result = fetch_network_info_fast()

        assert len(result.modules) == 2
        assert result.modules[0].manufacturer == "Intel"
        assert result.modules[0].vendor_id == "8086"
        assert result.modules[1].manufacturer == "Realtek"
        assert result.modules[1].vendor_id == "0BDA"

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_empty_output(self, mock_get_location_paths, mock_get_hardware_info):
        """Test handling of empty network hardware output"""

        def set_buffer(buffer, size):
            buffer.value = b""

        mock_get_hardware_info.side_effect = set_buffer

        result = fetch_network_info_fast()

        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.FAILED
        assert len(result.modules) == 0

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_malformed_output(self, mock_get_location_paths, mock_get_hardware_info):
        """Test handling of malformed output without pipes or equals"""
        wmi_output = "INVALID_DATA_NO_PROPER_FORMAT"

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer

        result = fetch_network_info_fast()

        assert isinstance(result, NetworkInfo)
        assert result.status.type == StatusType.SUCCESS
        assert len(result.modules) == 0

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_missing_manufacturer_field(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test handling when Manufacturer field is missing"""
        wmi_output = (
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_00000000|"
            "Name=Network Adapter\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.return_value = []

        result = fetch_network_info_fast()

        assert len(result.modules) == 1
        assert result.modules[0].manufacturer is None
        assert result.modules[0].name == "Network Adapter"
        assert result.modules[0].vendor_id == "8086"

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_location_paths_partial_list(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test handling when location_paths returns only one path instead of two"""
        wmi_output = (
            "Manufacturer=Intel|"
            "PNPDeviceID=PCI\\VEN_8086&DEV_1234&SUBSYS_00000000|"
            "Name=Intel Adapter\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        # Return only PCI path, no ACPI path
        mock_get_location_paths.return_value = ["PCIROOT(0)#PCI(0,0)"]

        result = fetch_network_info_fast()

        assert len(result.modules) == 1
        assert result.modules[0].pci_path is not None
        # ACPI path becomes empty string when second element is missing
        assert result.modules[0].acpi_path is None or result.modules[0].acpi_path == ""

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_location_paths_none_response(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test handling when get_location_paths returns None"""
        wmi_output = (
            "Manufacturer=Generic|"
            "PNPDeviceID=PCI\\VEN_1234&DEV_5678|"
            "Name=Generic NIC\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.return_value = None

        result = fetch_network_info_fast()

        assert len(result.modules) == 1
        assert result.status.type == StatusType.PARTIAL
        assert any(
            "Could not determine location paths" in msg
            for msg in result.status.messages
        )

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_usb_device_without_standard_ids(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test USB device without standard VID/PID format"""
        wmi_output = (
            "Manufacturer=Generic|"
            "PNPDeviceID=USB\\DEVICE_ID_123|"
            "Name=Generic USB Device\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.return_value = []

        result = fetch_network_info_fast()

        assert len(result.modules) == 1
        # No vendor_id or device_id extracted for non-standard format
        assert result.modules[0].vendor_id is None
        assert result.modules[0].device_id is None

    @patch("pysysinfo.dumps.windows.network.GetNetworkHardwareInfo")
    @patch("pysysinfo.dumps.windows.network.get_location_paths")
    def test_all_optional_fields_present(
        self, mock_get_location_paths, mock_get_hardware_info
    ):
        """Test parsing when all fields are present"""
        wmi_output = (
            "Manufacturer=Intel|"
            "PNPDeviceID=PCI\\VEN_8086&DEV_1F42&SUBSYS_00000000|"
            "Name=Intel Ethernet Controller|"
            "FriendlyName=Ethernet 1\n"
        )

        def set_buffer(buffer, size):
            buffer.value = wmi_output.encode("utf-8")

        mock_get_hardware_info.side_effect = set_buffer
        mock_get_location_paths.return_value = ["PCIROOT(0)#PCI(0,0)", "ACPI(_SB_)"]

        result = fetch_network_info_fast()

        assert len(result.modules) == 1
        module = result.modules[0]
        assert module.manufacturer == "Intel"
        assert module.name == "Intel Ethernet Controller"
        assert module.vendor_id == "8086"
        assert module.device_id == "1F42"
        assert module.pci_path is not None
        assert module.acpi_path is not None


class TestNetworkInfoModel:
    """Test suite for NetworkInfo and NICInfo models"""

    def test_network_info_default_initialization(self):
        """Test NetworkInfo initializes with empty modules list"""
        network_info = NetworkInfo()

        assert isinstance(network_info.modules, list)
        assert len(network_info.modules) == 0
        assert hasattr(network_info, "status")

    def test_nic_info_default_values(self):
        """Test NICInfo initializes with all None values"""
        nic = NICInfo()

        assert nic.name is None
        assert nic.device_id is None
        assert nic.vendor_id is None
        assert nic.acpi_path is None
        assert nic.pci_path is None
        assert nic.manufacturer is None

    def test_nic_info_custom_initialization(self):
        """Test NICInfo can be initialized with custom values"""
        nic = NICInfo(
            name="Intel I219-V",
            device_id="1F42",
            vendor_id="8086",
            manufacturer="Intel",
            acpi_path="ACPI(_SB_)#ACPI(PCI0)",
            pci_path="PCIROOT(0)#PCI(0,0)",
        )

        assert nic.name == "Intel I219-V"
        assert nic.device_id == "1F42"
        assert nic.vendor_id == "8086"
        assert nic.manufacturer == "Intel"
        assert nic.acpi_path == "ACPI(_SB_)#ACPI(PCI0)"
        assert nic.pci_path == "PCIROOT(0)#PCI(0,0)"

    def test_append_multiple_nics_to_network_info(self):
        """Test adding multiple NIC modules to NetworkInfo"""
        network_info = NetworkInfo()

        nic1 = NICInfo(name="Intel Ethernet", manufacturer="Intel", vendor_id="8086")
        nic2 = NICInfo(name="Realtek USB", manufacturer="Realtek", vendor_id="0BDA")

        network_info.modules.append(nic1)
        network_info.modules.append(nic2)

        assert len(network_info.modules) == 2
        assert network_info.modules[0].vendor_id == "8086"
        assert network_info.modules[1].vendor_id == "0BDA"

    def test_nic_info_partial_initialization(self):
        """Test NICInfo with only some fields set"""
        nic = NICInfo(name="Test NIC", vendor_id="1234")

        assert nic.name == "Test NIC"
        assert nic.vendor_id == "1234"
        assert nic.device_id is None
        assert nic.manufacturer is None
