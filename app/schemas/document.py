from pydantic import BaseModel
from uuid import UUID


class DocumentBase(BaseModel):
    name: str
    url: str


class DocumentCreate(DocumentBase):
    user_id: UUID
    size: int  # in bytes


class DocumentOut(DocumentBase):
    document_id: UUID
    user_id: UUID
    size: str  
    created: str

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v),
        }
