from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: str


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    created_at: datetime


class TaskUpdate(BaseModel):
    title: str
    description: str
