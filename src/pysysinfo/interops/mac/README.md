# MacDeviceInfo

A tiny macOS utility and shared library that enumerates every GPU in the system and reports extra Apple Silicon
details (core count, performance shaders, unified memory, etc.).
The native library lives in `src/`/`include/`, is exposed via a command-line tester (`main.cpp`), and also powers a thin
Python `ctypes` binding in `bindings/gpu_info.py`.

This is intended to be used via `gpu_info.py`. The CLI tool is primarily for testing and demonstration purposes, but it
can be used directly if desired.

Full disclosure: A big part of this C++ connector was written by Claude.
If you are someone with more know-how, and find lapses in this code, we'd be more than happy to welcome Pull Requests.

## Requirements

- macOS 10.9 (Mavericks) or newer on Intel
- macOS 11 (Big Sur) or newer on Apple Silicon
- Xcode Command Line Tools (provides clang and the IOKit/CoreFoundation headers)
- CMake 3.21+
- Python 3.7+ (for the `gpu_info.py` binding) - Assuming you want to compile this to use with PySysInfo.

## Build

```sh
cmake -S . -B build
cmake --build build
```

- `MacDeviceInfo` (the CLI tool) is emitted to `build/MacDeviceInfo`.
- `libdevice_info.dylib` is copied automatically into `bindings/` for the Python binding.
- The default deployment target is **macOS 10.9**. This is also the earliest version supported by Python 3.9,
  which is the minimum required for PySysInfo.
- The default build type is **Release**. Pass `-DCMAKE_BUILD_TYPE=Debug` to the first command to include debug symbols.
- To target a single architecture, add `-DCMAKE_OSX_ARCHITECTURES=arm64` or `x86_64` when generating the build tree.

## CLI Usage

```sh
./build/MacDeviceInfo
```

Sample output:

```
Found 1 GPU(s):

GPU 0:
  Name:         Apple M3 Pro
  Manufacturer: Apple Inc.
  Vendor ID:    0x106b
  Device ID:    0x0000
  Apple Silicon GPU:
    GPU Cores:     20
    Perf Shaders:  8
    GPU Gen:       15
    Unified Mem:   18432 MB
```

The tool exits with code `0` when enumeration succeeds, or `1` if the underlying IOKit call fails.

## Python Binding

After building the project once (so that `bindings/libdevice_info.dylib` exists), you can inspect GPUs from Python:

```sh
cd bindings
python3 gpu_info.py
```

or programmatically:

```python
from gpu_info import get_gpu_info

for idx, gpu in enumerate(get_gpu_info()):
    print(f"GPU {idx}:")
    print(gpu)
```

On import, the script loads the colocated `libdevice_info.dylib`; ensure you rebuild the CMake project whenever you make
changes to the native code.

## Troubleshooting

- **`libdevice_info.dylib not found`**: run the CMake build so the shared library is (re)generated in `bindings/`.
- **`get_gpu_info` returns -1**: verify that `MacDeviceInfo` has permission to query IOKit (sometimes fixed by rebooting
  after installing Xcode tools) and that you are running on macOS.
- **Python Unicode issues**: both the C and Python layers decode GPU names as UTF-8. Use `LANG=en_US.UTF-8` (default on
  macOS) if you see garbled characters.
