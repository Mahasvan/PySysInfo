#pragma once

#include <cstdint>
#include <string>
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>

// Converts a CFStringRef to a std::string (UTF-8). Returns empty on failure.
std::string readCFString(CFStringRef cfStr);

// Reads a uint32 value stored as CFData inside a CFDictionary.
uint32_t readUInt32(CFDictionaryRef dict, CFStringRef key);

// Reads a CFTypeRef (CFNumber or CFData) as a uint64_t. Returns 0 on failure.
uint64_t readCFTypeAsUInt64(CFTypeRef ref);

// Returns the appropriate IOKit main port for the running macOS version.
mach_port_t getIOKitMainPort();

// Reads a CFString value from a CFDictionary key. Returns empty if missing or wrong type.
std::string readCFStringFromDict(CFDictionaryRef dict, CFStringRef key);
