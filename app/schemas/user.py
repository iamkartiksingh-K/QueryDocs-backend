from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v)  # <- ensures UUID becomes a string
        }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
