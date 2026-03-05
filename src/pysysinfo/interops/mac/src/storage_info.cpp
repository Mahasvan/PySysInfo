#include "storage_info.h"
#include "iokit_helpers.h"

#include <cstring>
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>

// Recursively searches children of `entry` for a "Whole" IOMedia node.
// Returns its properties dictionary (caller must CFRelease), or nullptr if not found.
static CFMutableDictionaryRef findWholeMedia(io_service_t entry) {
    io_iterator_t iterator = 0;
    kern_return_t kr = IORegistryEntryGetChildIterator(entry, kIOServicePlane, &iterator);
    if (kr != KERN_SUCCESS || !iterator)
        return nullptr;

    io_service_t child;
    while ((child = IOIteratorNext(iterator)) != 0) {
        if (IOObjectConformsTo(child, "IOMedia")) {
            CFMutableDictionaryRef props = nullptr;
            if (IORegistryEntryCreateCFProperties(child, &props, kCFAllocatorDefault, kNilOptions) == KERN_SUCCESS &&
                props) {
                CFTypeRef wholeRef = CFDictionaryGetValue(props, CFSTR("Whole"));
                if (wholeRef && CFGetTypeID(wholeRef) == CFBooleanGetTypeID() &&
                    CFBooleanGetValue(static_cast<CFBooleanRef>(wholeRef))) {
                    IOObjectRelease(child);
                    IOObjectRelease(iterator);
                    return props;
                }
                CFRelease(props);
            }
        }

        // Recurse into children
        CFMutableDictionaryRef result = findWholeMedia(child);
        IOObjectRelease(child);
        if (result) {
            IOObjectRelease(iterator);
            return result;
        }
    }

    IOObjectRelease(iterator);
    return nullptr;
}

static void copyTrimmedString(const std::string &src, char *dst, size_t dst_size) {
    // Trim leading and trailing whitespace
    size_t start = src.find_first_not_of(" \t\n\r");
    size_t end = src.find_last_not_of(" \t\n\r");
    if (start == std::string::npos) {
        dst[0] = '\0';
        return;
    }
    std::string trimmed = src.substr(start, end - start + 1);
    std::strncpy(dst, trimmed.c_str(), dst_size - 1);
    dst[dst_size - 1] = '\0';
}

int get_storage_info(StorageDeviceProperties *out, int max_count) {
    if (!out || max_count <= 0) return -1;

    mach_port_t ioPort = getIOKitMainPort();

    CFMutableDictionaryRef matching = IOServiceMatching("IOBlockStorageDevice");
    if (!matching) return -1;

    io_iterator_t iterator = 0;
    kern_return_t kr = IOServiceGetMatchingServices(ioPort, matching, &iterator);
    if (kr != KERN_SUCCESS)
        return -1;

    int count = 0;
    io_service_t service;

    while ((service = IOIteratorNext(iterator)) != 0 && count < max_count) {
        CFMutableDictionaryRef props = nullptr;
        if (IORegistryEntryCreateCFProperties(service, &props, kCFAllocatorDefault, kNilOptions) != KERN_SUCCESS || !
            props) {
            IOObjectRelease(service);
            continue;
        }

        StorageDeviceProperties dev{};

        // Read "Device Characteristics" sub-dictionary
        CFTypeRef devCharRef = CFDictionaryGetValue(props, CFSTR("Device Characteristics"));
        if (devCharRef && CFGetTypeID(devCharRef) == CFDictionaryGetTypeID()) {
            auto devChar = static_cast<CFDictionaryRef>(devCharRef);

            std::string productName = readCFStringFromDict(devChar, CFSTR("Product Name"));
            copyTrimmedString(productName, dev.product_name, sizeof(dev.product_name));

            std::string vendorName = readCFStringFromDict(devChar, CFSTR("Vendor Name"));
            copyTrimmedString(vendorName, dev.vendor_name, sizeof(dev.vendor_name));

            std::string mediumType = readCFStringFromDict(devChar, CFSTR("Medium Type"));
            copyTrimmedString(mediumType, dev.medium_type, sizeof(dev.medium_type));
        }

        // Read "Protocol Characteristics" sub-dictionary
        CFTypeRef protoCharRef = CFDictionaryGetValue(props, CFSTR("Protocol Characteristics"));
        if (protoCharRef && CFGetTypeID(protoCharRef) == CFDictionaryGetTypeID()) {
            auto protoChar = static_cast<CFDictionaryRef>(protoCharRef);

            std::string interconnect = readCFStringFromDict(protoChar, CFSTR("Physical Interconnect"));
            copyTrimmedString(interconnect, dev.interconnect, sizeof(dev.interconnect));

            std::string location = readCFStringFromDict(protoChar, CFSTR("Physical Interconnect Location"));
            copyTrimmedString(location, dev.location, sizeof(dev.location));
        }

        // Find the "Whole" IOMedia child for disk size
        CFMutableDictionaryRef mediaProps = findWholeMedia(service);
        if (mediaProps) {
            CFTypeRef sizeRef = CFDictionaryGetValue(mediaProps, CFSTR("Size"));
            if (sizeRef)
                dev.size_bytes = readCFTypeAsUInt64(sizeRef);
            CFRelease(mediaProps);
        }

        // Only include entries that have at least a product name or device/protocol characteristics
        if (dev.product_name[0] != '\0' || dev.interconnect[0] != '\0') {
            out[count++] = dev;
        }

        CFRelease(props);
        IOObjectRelease(service);
    }

    IOObjectRelease(iterator);
    return count;
}
