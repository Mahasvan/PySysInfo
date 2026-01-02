from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class StatusType(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class Status(BaseModel):
    """This is the base class for all status models.
    Every component will have a ``status`` attribute,
    which is one of ``SuccessStatus``, ``PartialStatus`` or ``FailedStatus``.
    This class will not be used by any component as is."""
    type: StatusType = Field(default_factory=lambda: StatusType.SUCCESS)
    messages: List[str] = Field(default_factory=list)


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
