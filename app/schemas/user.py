from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"name": "alice"}})
    name: str


class UserRead(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "0uLvI2MYQL",
                "name": "alice",
                "created_at": "2026-06-28T06:03:23.931468",
            }
        }
    )
    id: str
    name: str
    created_at: datetime
