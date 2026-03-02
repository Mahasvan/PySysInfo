import plistlib
import re
import subprocess
from typing import List, Dict, Optional

from pysysinfo.models.network_models import NetworkInfo, NICInfo


def _fetch_controllers() -> List[str]:
    output = subprocess.run(["ipconfig", "getiflist"], capture_output=True)
    return output.stdout.decode("utf-8").strip().split(" ")

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

def _fetch_airport_details() -> Dict[str, NICInfo]:
    output = subprocess.run(["system_profiler", "SPAirPortDataType", "-xml"], capture_output=True)
    plist = plistlib.loads(output.stdout)
    res = {}
    ven_dev_pattern = re.compile(r"\((0[xX].{4}),\s?(0[xX].{4})\)")

    for item in plist:
        for wifi_card in item.get("_items", []):
            interfaces = wifi_card.get("spairport_airport_interfaces")
            for interface in interfaces:
                item = NICInfo()
                if "spairport_wireless_card_type" not in interface: continue
                # AWDL interfaces don't have this, and we want to skip them.

                card_type = interface["spairport_wireless_card_type"]
                match = ven_dev_pattern.findall(card_type)
                if not match: continue
                item.vendor_id = match[0][0]
                item.device_id = match[0][1]

                bsd_interface_name = interface.get("_name")
                res[bsd_interface_name] = item

    return res

def _fetch_system_profiler_details(valid_bsd_interfaces: List[str]) -> NetworkInfo:
    output = subprocess.run(["system_profiler", "SPNetworkDataType", "-xml"], capture_output=True)
    plist = plistlib.loads(output.stdout)
    network_info = NetworkInfo()

    ethernet_info: Optional[Dict[str, NICInfo]] = None
    airport_info: Optional[Dict[str, NICInfo]] = None

    for item in plist:
        for network_controller in item["_items"]:
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


def fetch_network_info():
    controllers = _fetch_controllers()

    return _fetch_system_profiler_details(controllers)
