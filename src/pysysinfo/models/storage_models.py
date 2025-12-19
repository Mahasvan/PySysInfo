from pydantic import BaseModel


class StorageSize(BaseModel):
    capacity: int

class Kilobyte(StorageSize):
    capacity: int = 0
    unit: str = "KB"

class Megabyte(StorageSize):
    capacity: int = 0
    unit: str = "MB"

class Gigabyte(StorageSize):
    capacity: int = 0
    unit: str = "GB"