from pydantic import BaseModel

from src.pysysinfo.models.success_models import SuccessStatus, StatusModel


class ComponentInfo(BaseModel):
    status: StatusModel = SuccessStatus()
