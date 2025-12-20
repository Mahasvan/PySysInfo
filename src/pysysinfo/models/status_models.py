from typing import List, Optional

from pydantic import BaseModel


class StatusModel(BaseModel):
    string: str
    messages: List[str]

class SuccessStatus(StatusModel):
    string: str = "success"
    messages: List[str] = []

class PartialStatus(StatusModel):
    string: str = "partial"
    messages: List[str] = []

class FailedStatus(StatusModel):
    string: str = "failed"
    messages: List[str] = []
