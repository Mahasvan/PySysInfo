#include <windows.h>
#include <dxgi1_6.h>
#include <WbemIdl.h>
#include <comutil.h>
#include <propvarutil.h>
#include <iostream>
#include <string>
#include <vector>

#pragma comment(lib, "dxgi.lib")
#pragma comment(lib, "wbemuuid.lib")
#pragma comment(lib, "comsuppw.lib")
#pragma comment(lib, "Propsys.lib")

typedef enum gpuHelper_Result_ENUM
{
    STATUS_OK = 0u,
    STATUS_NOK,
    STATUS_INVALID_ARG,
    STATUS_FAILURE
} gpuHelper_RESULT;

// Helper: convert wide string to char buffer
void ws2s(const WCHAR *wstr, char *buffer, int bufferSize)
{
    WideCharToMultiByte(CP_ACP, 0, wstr, -1, buffer, bufferSize, nullptr, nullptr);
}

// Helper: convert wide string to std::string
std::string WideToUtf8(PCWSTR src)
{
    if (!src || !*src)
        return {};

    int len = WideCharToMultiByte(
        CP_UTF8,
        0,
        src,
        -1,
        nullptr,
        0,
        nullptr,
        nullptr);

    if (len <= 1)
        return {};

    std::string out(len - 1, '\0');

    WideCharToMultiByte(
        CP_UTF8,
        0,
        src,
        -1,
        &out[0], // ✅ writable buffer
        len,
        nullptr,
        nullptr);

    return out;
}

// Core function
gpuHelper_RESULT GetGPUForDisplayInternal(const char *deviceName, char *outGPUName, unsigned int bufSize)
{
    if (deviceName == nullptr || strlen(deviceName) == 0)
    {
        return STATUS_INVALID_ARG;
    }

    if (outGPUName == nullptr)
    {
        return STATUS_INVALID_ARG;
    }

    if (bufSize <= 0)
    {
        return STATUS_INVALID_ARG;
    }

    IDXGIFactory6 *factory = nullptr;
    if (FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory))))
    {
        if (outGPUName && bufSize > 0)
            outGPUName[0] = 0;

        return STATUS_FAILURE;
    }

    IDXGIAdapter1 *adapter = nullptr;
    for (UINT a = 0; factory->EnumAdapters1(a, &adapter) != DXGI_ERROR_NOT_FOUND; ++a)
    {
        DXGI_ADAPTER_DESC1 descAdapter;
        if (FAILED(adapter->GetDesc1(&descAdapter)))
        {
            adapter->Release();
            continue;
        }

        IDXGIOutput *output = nullptr;
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
                    strncpy(outGPUName, outName, bufSize - 1);
                    outGPUName[bufSize - 1] = 0;
                }
                output->Release();
                adapter->Release();
                factory->Release();

                return STATUS_OK;
            }

            output->Release();
        }

        adapter->Release();
    }

    if (factory)
        factory->Release();
    if (outGPUName && bufSize > 0)
        outGPUName[0] = 0;

    // Parent GPU not found, return failure code
    return STATUS_FAILURE;
}

// DLL export
extern "C" __declspec(dllexport) gpuHelper_RESULT GetGPUForDisplay(const char *deviceName, char *outGPUName, int bufSize)
{
    return GetGPUForDisplayInternal(deviceName, outGPUName, bufSize);
}

extern "C" __declspec(dllexport) void GetWmiInfo(char *wmiQuery, char *cimServer, char *outBuffer, int maxLen)
{
    HRESULT hr;

    if (cimServer == nullptr || strlen(cimServer) == 0)
    {
        cimServer = "ROOT\\CIMV2";
    }

    hr = CoInitializeEx(0, COINIT_MULTITHREADED);
    if (FAILED(hr) && hr != RPC_E_CHANGED_MODE)
        return;

    hr = CoInitializeSecurity(NULL, -1, NULL, NULL, RPC_C_AUTHN_LEVEL_DEFAULT,
                              RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE, NULL);

    IWbemLocator *pLoc = NULL;
    hr = CoCreateInstance(CLSID_WbemLocator, 0, CLSCTX_INPROC_SERVER, IID_IWbemLocator, (LPVOID *)&pLoc);
    if (FAILED(hr))
    {
        CoUninitialize();
        return;
    }

    IWbemServices *pSvc = NULL;
    hr = pLoc->ConnectServer(_bstr_t(cimServer), NULL, NULL, 0, NULL, 0, 0, &pSvc);
    if (FAILED(hr))
    {
        pLoc->Release();
        CoUninitialize();
        return;
    }

    hr = CoSetProxyBlanket(pSvc, RPC_C_AUTHN_WINNT, RPC_C_AUTHZ_NONE, NULL,
                           RPC_C_AUTHN_LEVEL_CALL, RPC_C_IMP_LEVEL_IMPERSONATE, NULL, EOAC_NONE);

    IEnumWbemClassObject *pEnumerator = NULL;
    hr = pSvc->ExecQuery(bstr_t("WQL"),
                         bstr_t(wmiQuery),
                         WBEM_FLAG_FORWARD_ONLY | WBEM_FLAG_RETURN_IMMEDIATELY, NULL, &pEnumerator);

    if (SUCCEEDED(hr))
    {
        IWbemClassObject *pclsObj = NULL;
        ULONG uReturn = 0;
        std::string result = "";

        while (pEnumerator)
        {
            hr = pEnumerator->Next(WBEM_INFINITE, 1, &pclsObj, &uReturn);
            if (0 == uReturn)
                break;

            SAFEARRAY *pNames = nullptr;
            hr = pclsObj->GetNames(
                nullptr,
                WBEM_FLAG_NONSYSTEM_ONLY,
                nullptr,
                &pNames);

            if (SUCCEEDED(hr) && pNames)
            {
                LONG lBound = 0, uBound = -1;
                SafeArrayGetLBound(pNames, 1, &lBound);
                SafeArrayGetUBound(pNames, 1, &uBound);

                for (LONG i = lBound; i <= uBound; i++)
                {
                    BSTR propName = nullptr;
                    SafeArrayGetElement(pNames, &i, &propName);

                    VARIANT vtProp;
                    VariantInit(&vtProp);

                    if (SUCCEEDED(pclsObj->Get(propName, 0, &vtProp, nullptr, nullptr)))
                    {
                        WCHAR variantStr[1024] = {};
                        VariantToString(vtProp, variantStr, 1024);

                        result += (const char *)_bstr_t(propName);
                        result += "=";
                        result += WideToUtf8(variantStr);
                        result += "|";
                    }

                    VariantClear(&vtProp);
                    SysFreeString(propName);
                }

                result += "\n";
                SafeArrayDestroy(pNames);
            }

            pclsObj->Release();
        }

        strncpy_s(outBuffer, maxLen, result.c_str(), _TRUNCATE);
    }

    // Cleanup
    if (pEnumerator)
        pEnumerator->Release();
    pSvc->Release();
    pLoc->Release();
    CoUninitialize();
}