from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime


class TaskUpdate(BaseModel):
    title: str
    description: str
    status: str
    priority: str
