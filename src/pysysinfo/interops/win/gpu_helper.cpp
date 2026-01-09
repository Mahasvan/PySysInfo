#include <windows.h>
#include <dxgi1_6.h>
#include <string>

#pragma comment(lib, "dxgi.lib")

// Helper: convert wide string to char buffer
void ws2s(const WCHAR* wstr, char* buffer, int bufferSize)
{
    WideCharToMultiByte(CP_ACP, 0, wstr, -1, buffer, bufferSize, nullptr, nullptr);
}

// Core function
void GetGPUForDisplayInternal(const char* deviceName, char* outGPUName, int bufSize)
{
    IDXGIFactory6* factory = nullptr;
    if (FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory))))
    {
        if (outGPUName && bufSize > 0) outGPUName[0] = 0;
        return;
    }

    IDXGIAdapter1* adapter = nullptr;
    for (UINT a = 0; factory->EnumAdapters1(a, &adapter) != DXGI_ERROR_NOT_FOUND; ++a)
    {
        DXGI_ADAPTER_DESC1 descAdapter;
        if (FAILED(adapter->GetDesc1(&descAdapter)))
        {
            adapter->Release();
            continue;
        }

        IDXGIOutput* output = nullptr;
        for (UINT o = 0; adapter->EnumOutputs(o, &output) != DXGI_ERROR_NOT_FOUND; ++o)
        {
            DXGI_OUTPUT_DESC descOutput;
            if (FAILED(output->GetDesc(&descOutput)))
            {
                output->Release();
                continue;
            }

            char outName[128] = {};
            ws2s(descAdapter.Description, outName, sizeof(outName));

            char devName[32] = {};
            ws2s(descOutput.DeviceName, devName, sizeof(devName));

            if (strcmp(devName, deviceName) == 0)
            {
                if (outGPUName && bufSize > 0)
                {
                    strncpy(outGPUName, outName, bufSize-1);
                    outGPUName[bufSize-1] = 0;
                }
                output->Release();
                adapter->Release();
                factory->Release();
                return;
            }

            output->Release();
        }

        adapter->Release();
    }

    if (factory) factory->Release();
    if (outGPUName && bufSize > 0) outGPUName[0] = 0;
}

// DLL export
extern "C" __declspec(dllexport)
void GetGPUForDisplay(const char* deviceName, char* outGPUName, int bufSize)
{
    GetGPUForDisplayInternal(deviceName, outGPUName, bufSize);
}