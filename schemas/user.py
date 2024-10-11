from pydantic import BaseModel


class CreateUser(BaseModel):
    id: str
    username: str
    email: str
