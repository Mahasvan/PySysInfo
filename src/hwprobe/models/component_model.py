from hwprobe.models.status_models import Status
from pydantic import BaseModel, Field


class ComponentInfo(BaseModel):
    # Each component gets its own fresh status object
    status: Status = Field(default_factory=lambda: Status())
