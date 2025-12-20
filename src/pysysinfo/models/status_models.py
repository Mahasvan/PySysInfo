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

def make_partial_status(status: StatusModel, message: Optional[str]) -> None:
    if type(status) is not PartialStatus:
        status = PartialStatus()
    status.messages.append(message)