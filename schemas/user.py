from pydantic import BaseModel


class UserCreate(BaseModel):
    id: str
    given_name: str
    family_name: str
    username: str
    email: str
