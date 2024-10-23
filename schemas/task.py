from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: str
    user_id: str


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    created_at: datetime
