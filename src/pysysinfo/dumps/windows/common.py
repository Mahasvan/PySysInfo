import re


def format_acpi_path(raw_path: str) -> str:
    if not raw_path:
        return None

    # 1. Extract content inside ACPI(...) using Regex
    # This finds all occurrences of text between 'ACPI(' and ')'
    segments = re.findall(r'(ACPI|USB)\((.*?)\)', raw_path)

    if not segments:
        return raw_path  # Return original if no ACPI tags found

    # 2. Join with dots and prefix with the ACPI root backslash
    return "\\" + ".".join(seg[1] for seg in segments)


def format_pci_path(raw_path: str) -> str:
    if not raw_path:
        return None

    # Split the path into segments (separated by #)
    segments = raw_path.split("#")
    formatted_parts = []

    for seg in segments:
        # Match PCIROOT(n)
        root_match = re.match(r'PCIROOT\((\d+)\)', seg)
        if root_match:
            # Convert to Hex syntax like PciRoot(0x0)
            val = int(root_match.group(1))
            formatted_parts.append(f"PciRoot(0x{val:X})")
            continue

        # Match PCI(xxxx) or USB(xxxx) -> xxxx is Hex
        pci_match = re.match(r'(PCI|USB)\(([0-9A-Fa-f]+)\)', seg)
        if pci_match:
            # Parse the Hex string (e.g., '0801')
            full_val = int(pci_match.group(2), 16)

            # High 8 bits = Device, Low 8 bits = Function
            device = full_val >> 8
            function = full_val & 0xFF

            prefix = pci_match.group(1)

            formatted_parts.append(f"{prefix[0].upper() + prefix[1:].lower()}(0x{device:X},0x{function:X})")

    # Join with standard forward slash
    return "/".join(formatted_parts)
