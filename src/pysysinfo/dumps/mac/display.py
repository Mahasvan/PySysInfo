import json
import re
import subprocess
from typing import Tuple, Optional

from pysysinfo.dumps.common.edid import parse_edid
from pysysinfo.models.display_models import DisplayInfo, DisplayModuleInfo, ResolutionInfo


def _get_monitor_resolution_from_system_profiler(monitor_info: dict) -> Optional[Tuple[int, int]]:
    precedence = [
        "spdisplays_pixelresolution",
        "_spdisplays_pixels",
        "_spdisplays_resolution"
    ]

    resolution_regex = re.compile(r"(\d+)\s?x\s?(\d+)")

    for key in precedence:
        if resolution := resolution_regex.search(monitor_info.get(key, "")):
            return int(resolution.group(1)), int(resolution.group(2))
    return None


def _enrich_data_from_edid(monitor_info: DisplayModuleInfo, edid_string: str) -> DisplayModuleInfo:
    if edid_string.lower().startswith("0x"):
        edid_string = edid_string[2:]
    edid_bytes = bytes.fromhex(edid_string)
    data: DisplayModuleInfo = parse_edid(edid_bytes)
    for field in data.model_dump().keys():
        if monitor_info.__getattribute__(field) is None:
            monitor_info.__setattr__(field, data.__getattribute__(field))
    # Update the resolution as well
    if data.resolution is None: return monitor_info
    if monitor_info.resolution is None:
        monitor_info.resolution = data.resolution
        return monitor_info

    for field in data.resolution.model_dump().keys():
        if monitor_info.resolution.__getattribute__(field) is None:
            monitor_info.resolution.__setattr__(field, data.resolution.__getattribute__(field))
    return monitor_info


def _get_refresh_rate_from_system_profiler(monitor_info: dict) -> Optional[float]:
    precedence = [
        "spdisplays_pixelresolution"
        "_spdisplays_pixels",
        "_spdisplays_resolution"
    ]
    refresh_rate_regex = re.compile(r"([\d.]+)(?=Hz)")

    for key in precedence:
        if refresh_rate := refresh_rate_regex.search(monitor_info.get(key, "")):
            return float(refresh_rate.group(1))
    return None


def _fetch_monitor_info_system_profiler():
    monitors = []

    command = ["system_profiler", "-json", "SPDisplaysDataType"]

    try:
        output = json.loads(subprocess.run(command, capture_output=True, text=True).stdout)
    except (json.JSONDecodeError, FileNotFoundError):
        output = {}
    # todo: remove after testing
    with open("andrupka_profiler.json") as f:
        output = json.load(f)

    for display_controller in output.get("SPDisplaysDataType", []):
        monitor_instances = display_controller.get("spdisplays_ndrvs", [])
        for monitor in monitor_instances:
            monitor_info = DisplayModuleInfo()
            monitor_info.name = monitor.get("_name")

            retrieved_resolution = _get_monitor_resolution_from_system_profiler(monitor)
            retrieved_refresh_rate = _get_refresh_rate_from_system_profiler(monitor)
            res = ResolutionInfo()
            if retrieved_resolution:
                res.width, res.height = retrieved_resolution
            else:
                monitor_info.status.make_partial("Could not retrieve resolution from system profiler")
            if retrieved_refresh_rate:
                res.refresh_rate = retrieved_refresh_rate
            else:
                monitor_info.status.make_partial("Could not retrieve refresh rate from system profiler")
            monitor_info.resolution = res

            monitor_info.gpu_name = display_controller.get("sppci_model")
            if not monitor_info.gpu_name:
                monitor_info.gpu_name = display_controller.get("_name")
            if not monitor_info.gpu_name:
                monitor_info.status.make_partial("Could not retrieve GPU name from system profiler")

            if edid := monitor.get("_spdisplays_edid"):
                monitor_info = _enrich_data_from_edid(monitor_info, edid)

            monitors.append(monitor_info)

    return monitors


def fetch_display_info() -> DisplayInfo:
    display_info = DisplayInfo()
    display_info.modules = _fetch_monitor_info_system_profiler()

    return display_info
