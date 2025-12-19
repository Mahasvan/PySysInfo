from pydantic import BaseModel

from src.pysysinfo.models.status_models import SuccessStatus, StatusModel


class ComponentInfo(BaseModel):
    status: StatusModel = SuccessStatus()
