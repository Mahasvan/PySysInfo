import plistlib
import subprocess
from typing import List

from pysysinfo.models.network_models import NetworkInfo, NICInfo


def _fetch_controllers() -> List[str]:
    output = subprocess.run(["ipconfig", "getiflist"], capture_output=True)
    return output.stdout.decode("utf-8").strip().split(" ")


def _fetch_system_profiler_details(controllers: List[str]) -> NetworkInfo:
    output = subprocess.run(["system_profiler", "SPNetworkDataType", "-xml"], capture_output=True)
    plist = plistlib.loads(output.stdout)
    network_info = NetworkInfo()
    for item in plist:
        for network_controller in item["_items"]:
            module = NICInfo()

            interface = network_controller.get("interface")
            if interface not in controllers: continue

            module.interface = interface
            module.name = network_controller.get("_name", "")
            module.mac_address = network_controller.get("Ethernet", {}).get("MAC Address")
            if not module.mac_address:
                # Sometimes, unplugged devices also show up in system_profiler.
                continue
            module.type = network_controller.get("type")
            ip_addresses = network_controller.get("IPv4", {}).get("Addresses")
            if ip_addresses:
                module.ip_address = ip_addresses[0]

            network_info.modules.append(module)

    return network_info


def fetch_network_info():
    controllers = _fetch_controllers()
    return _fetch_system_profiler_details(controllers)
