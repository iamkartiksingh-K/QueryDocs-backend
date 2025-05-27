from pydantic import BaseModel

class DocumentBase(BaseModel):
    name: str
    url: str

class DocumentCreate(DocumentBase):
    user_id: int

class DocumentOut(DocumentBase):
    document_id: int
    user_id: int

    class Config:
        from_attributes = True
