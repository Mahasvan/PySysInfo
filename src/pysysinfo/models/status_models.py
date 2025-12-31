from typing import List, Optional

from pydantic import BaseModel, Field


class StatusModel(BaseModel):
    """This is the base class for all status models.
    Every component will have a ``status`` attribute,
    which is one of ``SuccessStatus``, ``PartialStatus`` or ``FailedStatus``.
    This class will not be used by any component as is."""
    string: str
    messages: List[str] = Field(default_factory=list)


class SuccessStatus(StatusModel):
    """StatusModel used when no issues were encountered during the discovery process.
    Messages may be present, containing information about the discovery process."""
    string: str = "success"
    messages: List[str] = Field(default_factory=list)


class PartialStatus(StatusModel):
    """
    StatusModel used when issues were encountered that partially hinder the discovery process.
    Messages may be present, containing information about the errors encountered.
    PartialStatus means that one or more attributes of the component were not fetched properly.
    """
    string: str = "partial"
    messages: List[str] = Field(default_factory=list)


class FailedStatus(StatusModel):
    """
    StatusModel used when a breaking issue was encountered during the discovery process.
    This means that no data could be discovered about the component.
    Messages may be present, containing information about the error.
    """
    string: str = "failed"
    messages: List[str] = Field(default_factory=list)

    def __init__(self, message: Optional[str] = None, messages: Optional[List[str]] = None):
        # Ensure each instance gets its own list
        base_messages = list(messages) if messages else []
        if message:
            base_messages.append(message)
        super().__init__(string="failed", messages=base_messages)


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
