# Original source:
# https://github.com/dortania/OpenCore-Legacy-Patcher/blob/ca859c7ad7ac2225af3b50626d88f3bfe014eaa8/resources/device_probe.py#L67-L93
# Copied from - https://github.com/KernelWanderers/OCSysInfo/blob/main/src/util/pci_root.py
from pysysinfo.dumps.mac.ioreg import *


def construct_pci_path_mac(parent_entry, acpi):
    data = {
        "pci_path": "",
        "acpi_path": ""
    }
    paths = []
    entry = parent_entry

    while entry:
        if IOObjectConformsTo(entry, b'IOPCIDevice'):
            try:
                bus, func = ([
                                 hex(int(i, 16)) for i in
                                 ioname_t_to_str(
                                     IORegistryEntryGetLocationInPlane(
                                         entry, b'IOService', None
                                     )[1]
                                 ).split(',')
                             ] + ['0x0'])[:2]

                paths.append(
                    f'Pci({bus},{func})'
                )
            except ValueError:
                break

        elif IOObjectConformsTo(entry, b'IOACPIPlatformDevice'):
            paths.append(
                f'PciRoot({hex(int(corefoundation_to_native(IORegistryEntryCreateCFProperty(entry, "_UID", kCFAllocatorDefault, kNilOptions)) or 0))})')
            break

        elif IOObjectConformsTo(entry, b'IOPCIBridge'):
            pass

        else:
            paths = []
            # Invalid PCI device – unable to construct PCI path
            break

        parent = IORegistryEntryGetParentEntry(entry, b'IOService', None)[1]

        if entry != parent_entry:
            IOObjectRelease(entry)

        entry = parent

    if paths:
        data['pci_path'] = '/'.join(reversed(paths))

    if acpi:
        data['acpi_path'] = ''.join([("\\" if "sb" in a.lower(
        ) else ".") + a.split("@")[0] for a in acpi.split(':')[1].split('/')[1:]])

    return data
