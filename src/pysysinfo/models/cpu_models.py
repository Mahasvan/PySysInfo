from typing import List, Optional

from src.pysysinfo.models.component_model import ComponentInfo


class CPUInfo(ComponentInfo):
    model_name: str = ""
    architecture: str = ""
    bitness: Optional[int] = None
    arch_version: Optional[str] = None
    vendor: Optional[str] = None
    sse_flags: List[str] = []
    cores: Optional[int] = None
    threads: Optional[int] = None