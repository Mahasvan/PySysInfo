from typing import List, Optional

from pysysinfo.models.component_model import ComponentInfo


class CPUInfo(ComponentInfo):
    model_name: Optional[str] = None
    architecture: Optional[str] = None
    bitness: Optional[int] = None
    arch_version: Optional[str] = None
    vendor: Optional[str] = None
    sse_flags: List[str] = []
    cores: Optional[int] = None
    threads: Optional[int] = None
