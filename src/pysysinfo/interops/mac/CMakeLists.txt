cmake_minimum_required(VERSION 3.21)
project(MacDeviceInfo LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Minimum deployment target: macOS 10.9 (Mavericks).
# Apple Silicon Macs always run macOS 11+, so the arm64 slice is unaffected.
if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif ()

if (NOT CMAKE_OSX_DEPLOYMENT_TARGET)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "10.9" CACHE STRING "Minimum macOS deployment target" FORCE)
endif ()

# Build a universal binary with both Apple Silicon and Intel slices.
# Override on the command line with -DCMAKE_OSX_ARCHITECTURES=arm64 or x86_64
# if you only want a single-arch build.
if (NOT CMAKE_OSX_ARCHITECTURES)
    set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "macOS target architectures" FORCE)
endif ()

find_library(IOKIT_FRAMEWORK IOKit REQUIRED)
find_library(COREFOUNDATION_FRAMEWORK CoreFoundation REQUIRED)

# ---- Shared library ----
add_library(device_info SHARED
        src/iokit_helpers.cpp
        src/gpu_info.cpp
        src/storage_info.cpp
)

target_include_directories(device_info
        PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(device_info
        PRIVATE
        ${IOKIT_FRAMEWORK}
        ${COREFOUNDATION_FRAMEWORK}
)

# Output the .dylib next to the Python binding
set_target_properties(device_info PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/bindings
)

# Use install_name_tool to change the install name after build
add_custom_command(TARGET device_info POST_BUILD
        COMMAND install_name_tool -id "@loader_path/libdevice_info.dylib"
        "${CMAKE_CURRENT_SOURCE_DIR}/bindings/libdevice_info.dylib"
        COMMENT "Updating install name for libdevice_info.dylib"
)

# ---- Standalone test executable ----
add_executable(MacDeviceInfo main.cpp)

target_include_directories(MacDeviceInfo
        PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(MacDeviceInfo
        PRIVATE
        device_info
)

# Configure the executable to find the dylib relative to its location
set_target_properties(MacDeviceInfo PROPERTIES
        BUILD_RPATH "${CMAKE_CURRENT_SOURCE_DIR}/bindings"
        INSTALL_RPATH "${CMAKE_CURRENT_SOURCE_DIR}/bindings"
)

# Copy dylib to the same directory as the executable after build
add_custom_command(TARGET MacDeviceInfo POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
        "${CMAKE_CURRENT_SOURCE_DIR}/bindings/libdevice_info.dylib"
        "$<TARGET_FILE_DIR:MacDeviceInfo>/libdevice_info.dylib"
        COMMENT "Copying libdevice_info.dylib next to executable"
)

