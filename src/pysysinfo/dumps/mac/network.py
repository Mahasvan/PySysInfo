import plistlib
import re
import subprocess
from typing import List, Dict, Optional

from pysysinfo.models.network_models import NetworkInfo, NICInfo


def _fetch_controllers() -> List[str]:
    output = subprocess.run(["ipconfig", "getiflist"], capture_output=True)
    stripped = output.stdout.decode("utf-8").strip()
    return stripped.split(" ") if stripped else []


def _fetch_ethernet_details() -> Dict[str, NICInfo]:
    output = subprocess.run(["system_profiler", "SPEthernetDataType", "-xml"], capture_output=True)
    plist = plistlib.loads(output.stdout)
    res = {}
    for item in plist:
        for ethernet_controller in item.get("_items", []):
            bsd_device_name = ethernet_controller.get("spethernet_BSD_Device_Name")

            info = NICInfo()
            info.vendor_id = ethernet_controller.get("spethernet_vendor-id")
            info.manufacturer = ethernet_controller.get("spethernet_vendor_name")
            info.device_id = ethernet_controller.get("spethernet_product-id")

            res[bsd_device_name] = info

    return res


def _find_child(children: list, key: str, value: str) -> Optional[dict]:
    """Find the first child dict where dict[key] == value."""
    return next((x for x in children if x and x.get(key) == value), None)


def _get_bsd_interface_apple_silicon(item: dict) -> Optional[str]:
    """
    Traverse the IORegistry tree for Apple Silicon Wi-Fi controllers:
    item
     └─ IORegistryEntryChildren
         └─ [IORegistryEntryName == "AppleBCMWLANSkywalkInterface"]
             └─ IORegistryEntryChildren
                 └─ [IOObjectClass == "IOSkywalkLegacyEthernet"]
                     └─ IORegistryEntryChildren
                         └─ [IOObjectClass == "IOSkywalkLegacyEthernetInterface"]
                             └─ IORegistryEntryName  →  "en0"
    """
    skywalk = _find_child(
        item.get("IORegistryEntryChildren", []),
        "IORegistryEntryName", "AppleBCMWLANSkywalkInterface"
    )
    if skywalk is None:
        return None

    legacy_ethernet = _find_child(
        skywalk.get("IORegistryEntryChildren", []),
        "IOObjectClass", "IOSkywalkLegacyEthernet"
    )
    if legacy_ethernet is None:
        return None

    legacy_interface = _find_child(
        legacy_ethernet.get("IORegistryEntryChildren", []),
        "IOObjectClass", "IOSkywalkLegacyEthernetInterface"
    )
    if legacy_interface is None:
        return None

    return legacy_interface.get("IORegistryEntryName")


def _fetch_airport_details() -> Dict[str, NICInfo]:
    """
    Earlier, `system_profiler SPAirPortDataType -xml` was used to get the vendor and device id.
    However, this was too slow, and we can get the same details from `ioreg`, while it being faster.
    """
    output = subprocess.run(["ioreg", "-c", "IO80211Controller", "-r", "-a"])
    plist = plistlib.loads(output.stdout)

    res = {}

    for item in plist:
        io_name_pattern = re.compile(r"pci([0-9a-fA-F]{4}),([0-9a-fA-F]{4})")

        driver = item.get("IORegistryEntryName")

        if not driver: return res

        if driver == "AirPort_BrcmNIC":
            # Intel Macs, usually
            io_name = item.get("IONameMatched", "")
            io_model = item.get("IOModel", "")
            match = io_name_pattern.match(io_name)
            vendor, device = match.groups()

            nic_info = NICInfo()
            nic_info.vendor_id = "0x" + vendor.upper()
            nic_info.device_id = "0x" + device.upper()
            if io_model: nic_info.name = io_model

            for child in item.get("IORegistryEntryChildren", []):
                if not child.get("IOObjectClass", "") == "AirPort_BrcmNIC_Interface":
                    continue
                bcm_identifier = child.get("IORegistryEntryName")
                res[bcm_identifier] = nic_info
                break

        elif driver == "AppleBCMWLANCore":
            # Apple Silicon Macs
            module_data = item.get("ModuleDictionary", {})
            nic_info = NICInfo()
            nic_info.vendor_id = hex(module_data.get("ManufacturerID", 0)).upper()
            nic_info.device_id = hex(module_data.get("ProductID", 0)).upper()

            bsd_identifier = _get_bsd_interface_apple_silicon(item)
            if bsd_identifier:
                res[bsd_identifier] = nic_info
        else:
            # todo: Implement for drivers such as AirPortAtheros40, AirPortBrcm4331, AirPortBrcm4360
            print("Unknown driver: ", driver)
            print("Please contact developer with this information to help improve support for your machine.")
            continue

    return res


def _fetch_system_profiler_details(valid_bsd_interfaces: List[str]) -> NetworkInfo:
    output = subprocess.run(["system_profiler", "SPNetworkDataType", "-xml"], capture_output=True)
    plist = plistlib.loads(output.stdout)
    network_info = NetworkInfo()

    ethernet_info: Optional[Dict[str, NICInfo]] = None
    airport_info: Optional[Dict[str, NICInfo]] = None

    for item in plist:
        for network_controller in item.get("_items", []):
            module = NICInfo()

            bsd_interface_name = network_controller.get("interface")
            if bsd_interface_name not in valid_bsd_interfaces: continue

            module.interface = bsd_interface_name
            module.name = network_controller.get("_name", "")
            module.mac_address = network_controller.get("Ethernet", {}).get("MAC Address")
            if not module.mac_address:
                # Sometimes, unplugged devices also show up in system_profiler.
                # todo: Still, some unplugged devices show up, which have duplicated MAC addresses.
                # Can we prune them? They show up in System Information too though, so not a dealbreaker.
                continue
            module.type = network_controller.get("type")
            # todo: Make this an ENUM and share with other OSes
            ip_addresses = network_controller.get("IPv4", {}).get("Addresses")
            if ip_addresses:
                module.ip_address = ip_addresses[0]

            if module.type == 'Ethernet':
                if ethernet_info is None: ethernet_info = _fetch_ethernet_details()
                if bsd_interface_name in ethernet_info:
                    module.vendor_id = ethernet_info[bsd_interface_name].vendor_id
                    module.manufacturer = ethernet_info[bsd_interface_name].manufacturer
                    module.device_id = ethernet_info[bsd_interface_name].device_id

            elif module.type == 'AirPort':
                if airport_info is None: airport_info = _fetch_airport_details()
                if bsd_interface_name in airport_info:
                    module.vendor_id = airport_info[bsd_interface_name].vendor_id
                    module.device_id = airport_info[bsd_interface_name].device_id

            network_info.modules.append(module)

    return network_info


def fetch_network_info() -> NetworkInfo:
    controllers = _fetch_controllers()
    return _fetch_system_profiler_details(controllers)
