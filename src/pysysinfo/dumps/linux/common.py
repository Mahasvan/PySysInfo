import os

# Source: https://github.com/KernelWanderers/OCSysInfo/blob/main/src/util/pci_root.py


def pci_from_acpi_linux(device_path):
    acpi_path = os.path.join(device_path, "firmware_node", "path")
    uevent_path = os.path.join(device_path, "uevent")

    try:
        with open(acpi_path, "r") as f:
            acpi = f.read().strip()
        with open(uevent_path, "r") as f:
            pci_uevent = f.read().strip()
    except (OSError, IOError):
        return None, None

    if not (acpi and pci_uevent):
        return None, None

    # Extract PCI slot name from uevent
    # Format: <domain>:<bus>:<slot>.<function>
    slot = None
    for line in pci_uevent.splitlines():
        if line.lower().startswith("pci_slot_name="):
            slot = line.split("=", 1)[1]
            break

    if not slot:
        return acpi, ""

    # Construct PCI path
    # E.g: PciRoot(0x0)/Pci(0x2,0x0)
    try:
        domain = int(slot.split(":")[0], 16)
        pci_path = f"PciRoot({hex(domain)})"
    except (IndexError, ValueError):
        return acpi, ""

    # Collect path components (current device and parents)
    paths = []

    # Add current device
    current_components = _get_address_components(slot)
    if current_components:
        paths.append(",".join(current_components))

    # Find parent bridges
    # Check if 'slot' is listed in the directory of other devices
    pci_root = "/sys/bus/pci/devices"
    if os.path.exists(pci_root):
        for device_name in os.listdir(pci_root):
            device_dir = os.path.join(pci_root, device_name)
            try:
                if slot in os.listdir(device_dir):
                    parent_components = _get_address_components(device_name)
                    if parent_components:
                        paths.append(",".join(parent_components))
            except OSError:
                continue

    # Sort paths and append to pci_path
    # Note: Sorting logic preserved from original code
    for comp in sorted(paths, reverse=True):
        pci_path += f"/Pci({comp})"

    return acpi, pci_path


def _get_address_components(slot_name):
    """
    Parses PCI slot name (domain:bus:device.function)
    and returns a tuple of hex strings (device, function).
    """
    try:
        # slot_name example: 0000:00:1f.3
        # split(":")[-1] -> 1f.3
        # split(".") -> ['1f', '3']
        device_func = slot_name.split(":")[-1]
        return tuple(hex(int(n, 16)) for n in device_func.split("."))
    except (ValueError, IndexError, AttributeError):
        return None