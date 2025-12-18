from typing import List

from src.pysysinfo.models.component_model import ComponentInfo


class CPUInfo(ComponentInfo):
    model_name: str = ""
    vendor: str = ""
    flags: List[str] = []
    cores: int = -1
    threads: int = -1