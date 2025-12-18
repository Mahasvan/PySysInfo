from typing import List, Optional

from src.pysysinfo.models.component_model import ComponentInfo


class CPUInfo(ComponentInfo):
    model_name: str = ""
    architecture: str = ""
    version: Optional[str] = None
    vendor: Optional[str] = None
    flags: List[str] = []
    cores: Optional[int] = None
    threads: int = -1