from pydantic import BaseModel


class StatusModel(BaseModel):
    string: str

class SuccessStatus(StatusModel):
    string: str = "success"

class PartialStatus(StatusModel):
    string: str = "partial"

class FailedStatus(StatusModel):
    string: str = "failed"