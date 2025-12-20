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
if type(cpu_info.status) is PartialStatus:
    cpu_info.status.messages.append("My New Debug Message")
else:
    cpu_info.status = PartialStatus(messages=["My New Debug Message"])]
```
"""