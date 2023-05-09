from typing import Optional, ClassVar
from datetime import datetime
from pydantic import BaseModel, validator


class BaseDoc(BaseModel):
    id: str
    content: str
    timestamp: datetime
    source: ClassVar[str] = "doc"

    @validator("timestamp", pre=True)
    def parse_timestamp(cls, value):
        if isinstance(value, int):
            return datetime.fromtimestamp(value)
        elif isinstance(value, datetime):
            return value
        else:
            raise ValueError("timestamp must be int or datetime")

    class Config:
        json_encoders = {
            datetime: lambda dt: int(dt.timestamp()),
        }


# create discord message model
class Discord(BaseDoc):
    author: str
    channel_id: str
    source: ClassVar[str] = "discord"
