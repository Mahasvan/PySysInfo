from pydantic import BaseModel, Field

from pysysinfo.models.status_models import Status, StatusType


class ComponentInfo(BaseModel):
    # Each component gets its own fresh status object
    status: Status = Field(default_factory=lambda: Status())
