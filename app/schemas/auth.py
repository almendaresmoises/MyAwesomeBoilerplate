from pydantic import BaseModel, EmailStr
from uuid import UUID

class Token(BaseModel):
    access_token: str
    refresh_token: str #remove
    token_type: str = "bearer"

class Login(BaseModel):
    email: EmailStr
    password: str
