from pydantic import BaseModel


class StatusModel(BaseModel):
    status: str

class SuccessStatus(StatusModel):
    status: str = "success"

class PartialStatus(StatusModel):
    status: str = "partial"

class FailedStatus(StatusModel):
    status: str = "failed"