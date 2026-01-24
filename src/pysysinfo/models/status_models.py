from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class StatusType(Enum):
    """Types of statuses possible."""

    #: There were no errors encountered.
    SUCCESS = "success"
    #: There were errors encountered, but only some parts of the data could not be retrieved.
    PARTIAL = "partial"
    #: Fatal error occurred, no data was able to be retrieved.
    FAILED = "failed"


class Status(BaseModel):
    """
    Describes the status of an individual component.
    If the status is ``PARTIAL`` or ``FAILED``, there may be messages that describe the error(s).
    """
    type: StatusType = Field(default_factory=lambda: StatusType.SUCCESS)
    messages: List[str] = Field(default_factory=list)

    def make_partial(self, message: str = None) -> None:
        self.type = StatusType.PARTIAL
        if message: self.messages.append(message)


"""
The intention of `messages` being List[str] is that PartialStatus can benefit from containing many messages.

When changing the status of a component to PartialStatus(), we do the following.
```
cpu_info.status = PartialStatus(messages=cpu_info.status.messages))
cpu_info.status.messages.append("My New Debug Message")
```

This is done because cpu_info.status may be an instance of SuccessStatus or PartialStatus.
if it is FailureStatus, the discovery of that component would have probably stopped after reaching the failure state.

The above code snippet can be replaced with the below snippet, and would yield the same result. 
```
if isinstance(cpu_info.status, PartialStatus):
    cpu_info.status.messages.append("My New Debug Message")
else:
    cpu_info.status = PartialStatus(messages=["My New Debug Message"])]
```
"""
