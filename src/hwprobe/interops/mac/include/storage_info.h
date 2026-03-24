#pragma once

#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    char product_name[256];
    char vendor_name[256];
    char medium_type[128]; // e.g. "Solid State", "Rotational"
    char interconnect[128]; // e.g. "PCI-Express", "SATA", "USB"
    char location[64]; // e.g. "Internal", "External"
    char bsd_name[64]; // e.g. "disk0", "disk1"
    uint64_t size_bytes; // Total disk size from IOMedia
} StorageDeviceProperties;

// Fills `out` with storage device entries. Returns the number of devices found, or -1 on error.
int get_storage_info(StorageDeviceProperties *out, int max_count);

#ifdef __cplusplus
}
#endif