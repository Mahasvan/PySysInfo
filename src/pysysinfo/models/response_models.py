from typing import List

from pydantic import BaseModel


class HardwareInfo(BaseModel):
    cpu: CPUResponse

class LinuxHardwareInfo(HardwareInfo):
    cpu: CPUResponse


class CPUResponse(BaseModel):
    model_name: str = ""
    vendor: str = ""
    flags: List[str] = []
    cores: int = -1
    threads: int = -1