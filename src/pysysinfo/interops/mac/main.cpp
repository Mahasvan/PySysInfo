#include <iostream>
#include <iomanip>
#include "gpu_info.h"

int main() {
    GPUProperties gpus[16];
    int count = get_gpu_info(gpus, 16);

    if (count < 0) {
        std::cerr << "Failed to retrieve GPU info.\n";
        return 1;
    }

    std::cout << "Found " << count << " GPU(s):\n\n";

    for (int i = 0; i < count; ++i) {
        const GPUProperties& g = gpus[i];
        std::cout << "GPU " << i << ":\n";
        std::cout << "  Name:         " << g.name << "\n";
        std::cout << "  Manufacturer: " << g.manufacturer << "\n";
        std::cout << std::hex << std::setfill('0');
        std::cout << "  Vendor ID:    0x" << std::setw(4) << g.vendor_id << "\n";
        std::cout << "  Device ID:    0x" << std::setw(4) << g.device_id << "\n";
        std::cout << std::dec << std::setfill(' ');
        if (g.is_apple_silicon) {
            std::cout << "  Apple Silicon GPU:\n";
            std::cout << "    GPU Cores:     " << g.apple_gpu.core_count << "\n";
            std::cout << "    Perf Shaders:  " << g.apple_gpu.gpu_perf_shaders << "\n";
            std::cout << "    GPU Gen:       " << g.apple_gpu.gpu_gen << "\n";
            std::cout << "    Unified Mem:   " << g.apple_gpu.unified_memory_mb << " MB\n";
        }
        std::cout << "\n";
    }

    return 0;
}
