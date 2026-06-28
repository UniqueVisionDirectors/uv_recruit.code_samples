from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str


class UserRead(BaseModel):
    id: str
    name: str
    created_at: datetime
