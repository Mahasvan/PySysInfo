#include "gpu_info.h"

#include <cstdint>
#include <string>
#include <cstring>
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <sys/sysctl.h>

// ---- Internal helpers ----

static uint32_t readUInt32(const CFDictionaryRef dict, const CFStringRef key) {
    const CFTypeRef ref = CFDictionaryGetValue(dict, key);
    if (!ref || CFGetTypeID(ref) != CFDataGetTypeID())
        return 0;
    uint32_t value = 0;
    CFIndex len = CFDataGetLength(static_cast<CFDataRef>(ref));
    if (len > 0) {
        CFDataGetBytes(static_cast<CFDataRef>(ref),
                       CFRangeMake(0, std::min(static_cast<CFIndex>(sizeof(value)), len)),
                       reinterpret_cast<UInt8 *>(&value));
    }
    return value;
}

static std::string readCFString(CFStringRef cfStr) {
    if (!cfStr) return {};
    if (const char *cStr = CFStringGetCStringPtr(cfStr, kCFStringEncodingUTF8))
        return {cStr};
    CFIndex length = CFStringGetLength(cfStr);
    if (length == 0) return {};
    CFIndex maxSize = CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8) + 1;
    std::string result(static_cast<size_t>(maxSize), '\0');
    if (CFStringGetCString(cfStr, result.data(), maxSize, kCFStringEncodingUTF8)) {
        result.resize(std::strlen(result.c_str()));
        return result;
    }
    return {};
}

static int getAppleGpuProperty(CFDictionaryRef gpuConfig, CFStringRef key) {
    int result = 0;
    CFTypeRef value = CFDictionaryGetValue(gpuConfig, key);
    if (value && CFGetTypeID(value) == CFNumberGetTypeID())
        CFNumberGetValue(static_cast<CFNumberRef>(value), kCFNumberIntType, &result);
    return result;
}

static uint64_t getSystemMemoryMB() {
    int mib[2] = {CTL_HW, HW_MEMSIZE};
    uint64_t mem = 0;
    size_t length = sizeof(mem);
    if (sysctl(mib, 2, &mem, &length, nullptr, 0) == 0)
        return mem / (1024 * 1024);
    return 0;
}

static CFDictionaryRef buildMatchingDict(bool is_arm) {
    if (is_arm) {
        const void *keys[] = {CFSTR("IONameMatched")};
        const void *values[] = {CFSTR("gpu*")};
        return CFDictionaryCreate(kCFAllocatorDefault, keys, values, 1,
                                  &kCFTypeDictionaryKeyCallBacks,
                                  &kCFTypeDictionaryValueCallBacks);
    } else {
        const void *keys[] = {CFSTR("IOProviderClass"), CFSTR("IOPCIClassMatch")};
        const void *values[] = {CFSTR("IOPCIDevice"), CFSTR("0x03000000&0xff000000")};
        return CFDictionaryCreate(kCFAllocatorDefault, keys, values, 2,
                                  &kCFTypeDictionaryKeyCallBacks,
                                  &kCFTypeDictionaryValueCallBacks);
    }
}

// ---- Public API ----

int get_gpu_info(GPUProperties *out, int max_count) {
    if (!out || max_count <= 0) return -1;

#if defined(__arm64__)
    constexpr bool is_arm = true;
#else
    constexpr bool is_arm = false;
#endif

    mach_port_t ioPort;
    if (__builtin_available(macOS 12.0, *))
        ioPort = kIOMainPortDefault;
    else
        ioPort = kIOMasterPortDefault;

    // NOTE: IOServiceGetMatchingServices takes ownership of the matching dict
    // (it always calls CFRelease internally), so we must not release it ourselves.
    CFDictionaryRef matching = buildMatchingDict(is_arm);
    io_iterator_t iterator = 0;
    kern_return_t kr = IOServiceGetMatchingServices(ioPort, matching, &iterator);
    if (kr != KERN_SUCCESS)
        return -1;

    int count = 0;
    io_service_t service;

    while ((service = IOIteratorNext(iterator)) != 0 && count < max_count) {
        CFMutableDictionaryRef props = nullptr;
        if (IORegistryEntryCreateCFProperties(service, &props, kCFAllocatorDefault, kNilOptions) != KERN_SUCCESS) {
            IOObjectRelease(service);
            continue;
        }

        // Filter non-GPU entries on ARM
        if (is_arm) {
            std::string ioName = readCFString(
                static_cast<CFStringRef>(CFDictionaryGetValue(props, CFSTR("IONameMatched"))));
            std::string bundle = readCFString(
                static_cast<CFStringRef>(CFDictionaryGetValue(props, CFSTR("CFBundleIdentifierKernel"))));
            if (ioName.find("gpu") == std::string::npos && bundle.find("AGX") == std::string::npos) {
                CFRelease(props);
                IOObjectRelease(service);
                continue;
            }
        }

        GPUProperties gpu{};
        gpu.vendor_id = readUInt32(props, CFSTR("vendor-id"));
        gpu.device_id = readUInt32(props, CFSTR("device-id"));

        CFTypeRef modelRef = CFDictionaryGetValue(props, CFSTR("model"));
        if (modelRef) {
            if (CFGetTypeID(modelRef) == CFStringGetTypeID()) {
                // Apple Silicon / some entries expose model as CFString
                std::string n = readCFString(static_cast<CFStringRef>(modelRef));
                std::strncpy(gpu.name, n.c_str(), sizeof(gpu.name) - 1);
            } else if (CFGetTypeID(modelRef) == CFDataGetTypeID()) {
                // PCI GPUs (AMD, NVIDIA, Intel) store model as a null-terminated
                // byte sequence inside a CFData blob
                auto data = static_cast<CFDataRef>(modelRef);
                CFIndex len = CFDataGetLength(data);
                if (len > 0) {
                    CFIndex copy = std::min(len, static_cast<CFIndex>(sizeof(gpu.name) - 1));
                    CFDataGetBytes(data, CFRangeMake(0, copy),
                                   reinterpret_cast<UInt8 *>(gpu.name));
                    gpu.name[copy] = '\0';
                }
            }
        }

        if (gpu.name[0] != '\0' || gpu.vendor_id != 0) {
            if (is_arm) {
                std::strncpy(gpu.manufacturer, "Apple Inc.", sizeof(gpu.manufacturer) - 1);
                gpu.is_apple_silicon = 1;
                gpu.apple_gpu.unified_memory_mb = getSystemMemoryMB();

                CFTypeRef configRef = CFDictionaryGetValue(props, CFSTR("GPUConfigurationVariable"));
                if (configRef && CFGetTypeID(configRef) == CFDictionaryGetTypeID()) {
                    auto gpuConfig = static_cast<CFDictionaryRef>(configRef);
                    gpu.apple_gpu.core_count = getAppleGpuProperty(gpuConfig, CFSTR("num_cores"));
                    gpu.apple_gpu.gpu_perf_shaders = getAppleGpuProperty(gpuConfig, CFSTR("num_gps"));
                    gpu.apple_gpu.gpu_gen = getAppleGpuProperty(gpuConfig, CFSTR("gpu_gen"));
                }
            } else {
                gpu.is_apple_silicon = 0;
                const char *mfr = "Unknown";
                if (gpu.vendor_id == 0x8086) mfr = "Intel";
                else if (gpu.vendor_id == 0x1002) mfr = "AMD";
                else if (gpu.vendor_id == 0x10DE) mfr = "NVIDIA";
                std::strncpy(gpu.manufacturer, mfr, sizeof(gpu.manufacturer) - 1);
            }
            out[count++] = gpu;
        }

        CFRelease(props);
        IOObjectRelease(service);
    }

    IOObjectRelease(iterator);
    return count;
}

