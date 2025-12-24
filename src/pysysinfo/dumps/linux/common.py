import os

# Source: https://github.com/KernelWanderers/OCSysInfo/blob/main/src/util/pci_root.py


def pci_from_acpi_linux(device_path):
    acpi = ""
    pci = ""

    try:
        acpi = open(f"{device_path}/firmware_node/path", "r").read().strip()
        pci = open(f"{device_path}/uevent", "r").read().strip()

    except:
        return None, None

    if not (acpi and pci):
        return None, None

    # Path to be yielded in the end.
    # E.g: PciRoot(0x0)/Pci(0x2,0x0)
    pci_path = ""

    # Parent PCI description
    #
    # <domain>:<bus>:<slot>.<function>
    slot = ""

    for line in pci.split("\n"):
        if "pci_slot_name" in line.lower():
            slot = line.split("=")[1]
            break

    if slot:
        # Domain
        pci_path += f"PciRoot({hex(int(slot.split(':')[0], 16))})"
        children = []
        paths = [",".join(_get_valid(slot))]

        for path in os.listdir("/sys/bus/pci/devices"):
            if slot in os.listdir(f"/sys/bus/pci/devices/{path}"):
                children.append(path)

        for child in children:
            paths.append(",".join(_get_valid(child)))

        for comp in sorted(paths, reverse=True):
            pci_path += f"/Pci({comp})"

    return acpi, pci_path

def _get_valid(slot):
    try:
        return tuple([
            hex(
                int(n, 16)) for n
            in slot.split(":")[-1].split(".")
        ])
    except:
        return None, None