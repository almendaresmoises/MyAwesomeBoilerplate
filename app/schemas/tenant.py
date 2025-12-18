from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    tenant_id: UUID 

class UserOut(BaseModel):
    user_id: UUID
    email: EmailStr
    role: str
    tenant_id: UUID

    class Config:
        orm_mode = True
