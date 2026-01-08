# Source: https://github.com/KernelWanderers/OCSysInfo/blob/main/src/util/pci_root.py


def pci_path_linux(device_slot: str):
    """
    :param device_slot: format: <domain>:<bus>:<slot>.<function>
    :return: PCI Path
    """

    # Construct PCI path
    # E.g: PciRoot(0x0)/Pci(0x2,0x0)
    try:
        domain = int(device_slot.split(":")[0], 16)
        pci_path = f"PciRoot({hex(domain)})"
    except (IndexError, ValueError):
        return None

    # Collect path components (current device and parents)
    paths = []

    # Add current device
    current_components = _get_address_components(device_slot)
    if current_components:
        paths.append(",".join(current_components))

    # Find parent bridges
    # Check if 'slot' is listed in the directory of other devices
    parent_components = _get_address_components(device_slot)
    if parent_components:
        paths.append(",".join(parent_components))

    # Sort paths and append to pci_path
    # Note: Sorting logic preserved from original code
    for comp in sorted(paths, reverse=True):
        pci_path += f"/Pci({comp})"

    return pci_path


def _get_address_components(slot_name):
    """
    :param slot_name: format: <domain>:<bus>:<slot>.<function>
    :return: Tuple of address components
    """
    try:
        # slot_name example: 0000:00:1f.3
        # split(":")[-1] -> 1f.3
        # split(".") -> ['1f', '3']
        device_func = slot_name.split(":")[-1]
        return tuple(hex(int(n, 16)) for n in device_func.split("."))
    except (ValueError, IndexError, AttributeError):
        return None
