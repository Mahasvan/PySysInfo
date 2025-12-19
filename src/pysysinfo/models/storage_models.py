from pydantic import BaseModel


class StorageSize(BaseModel):
    capacity: int

class Kilobyte(StorageSize):
    capacity: int
    unit: str = "KB"

class Megabyte(StorageSize):
    capacity: int
    unit: str = "MB"

class Gigabyte(StorageSize):
    capacity: int
    unit: str = "GB"