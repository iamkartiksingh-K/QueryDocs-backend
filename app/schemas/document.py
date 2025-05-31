from pydantic import BaseModel
from uuid import UUID

class DocumentBase(BaseModel):
    name: str
    url: str

class DocumentCreate(DocumentBase):
    user_id: UUID

class DocumentOut(DocumentBase):
    document_id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v)  # <- ensures UUID becomes a string
        }
